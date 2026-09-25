from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from django.conf import settings


class UnsafeArticleURLError(ValueError):
    pass


class ArticleFetchError(RuntimeError):
    pass


@dataclass(slots=True)
class ArticleDocument:
    url: str
    final_url: str
    title: str
    content: str
    content_type: str


def _default_resolver(
    hostname: str,
) -> list[str]:
    results = socket.getaddrinfo(
        hostname,
        None,
        type=socket.SOCK_STREAM,
    )

    return list(
        {
            item[4][0]
            for item in results
        }
    )


def _is_public_ip(
    value: str,
) -> bool:
    ip = ipaddress.ip_address(
        value
    )

    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_public_http_url(
    url: str,
    *,
    resolver:
        Callable[
            [str],
            list[str],
        ] = _default_resolver,
) -> None:
    parsed = urlparse(
        url
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise UnsafeArticleURLError(
            "Yalnizca http/https URL'leri "
            "desteklenir."
        )

    if (
        parsed.username
        or parsed.password
    ):
        raise UnsafeArticleURLError(
            "Kimlik bilgisi iceren URL "
            "desteklenmez."
        )

    hostname = (
        parsed.hostname
        or ""
    ).strip().lower()

    if not hostname:
        raise UnsafeArticleURLError(
            "URL hostname icermiyor."
        )

    if hostname in {
        "localhost",
        "localhost.localdomain",
    }:
        raise UnsafeArticleURLError(
            "Localhost adresleri engellendi."
        )

    try:
        addresses = resolver(
            hostname
        )
    except OSError as exc:
        raise UnsafeArticleURLError(
            "Hostname cozumlenemedi."
        ) from exc

    if not addresses:
        raise UnsafeArticleURLError(
            "Hostname icin IP bulunamadi."
        )

    for address in addresses:
        try:
            public = _is_public_ip(
                address
            )
        except ValueError as exc:
            raise UnsafeArticleURLError(
                "Gecersiz IP adresi."
            ) from exc

        if not public:
            raise UnsafeArticleURLError(
                "Private veya local IP "
                "adreslerine erisim engellendi."
            )


class ArticleContentFetcher:
    def __init__(
        self,
        *,
        timeout: float | None = None,
        max_bytes: int | None = None,
        max_redirects: int | None = None,
        min_chars: int | None = None,
        client: httpx.Client | None = None,
        resolver:
            Callable[
                [str],
                list[str],
            ] = _default_resolver,
    ):
        self.timeout = (
            settings.EVIDENCE_HTTP_TIMEOUT_SECONDS
            if timeout is None
            else timeout
        )

        self.max_bytes = (
            settings.ARTICLE_FETCH_MAX_BYTES
            if max_bytes is None
            else max_bytes
        )

        self.max_redirects = (
            settings.ARTICLE_FETCH_MAX_REDIRECTS
            if max_redirects is None
            else max_redirects
        )

        self.min_chars = (
            settings.ARTICLE_CONTENT_MIN_CHARS
            if min_chars is None
            else min_chars
        )

        self.client = client
        self.resolver = resolver

    def _request(
        self,
        url: str,
    ) -> httpx.Response:
        headers = {
            "User-Agent": (
                "VERITAS-EvidenceBot/1.0 "
                "(research fact-checking)"
            ),
            "Accept": (
                "text/html,"
                "application/xhtml+xml"
            ),
        }

        if self.client is not None:
            return self.client.get(
                url,
                headers=headers,
                follow_redirects=False,
            )

        return httpx.get(
            url,
            headers=headers,
            timeout=self.timeout,
            follow_redirects=False,
        )

    def _fetch_response(
        self,
        url: str,
    ) -> tuple[
        httpx.Response,
        str,
    ]:
        current_url = url

        for redirect_count in range(
            self.max_redirects + 1
        ):
            validate_public_http_url(
                current_url,
                resolver=self.resolver,
            )

            try:
                response = self._request(
                    current_url
                )
            except httpx.HTTPError as exc:
                raise ArticleFetchError(
                    "Makale indirilemedi."
                ) from exc

            if response.status_code in {
                301,
                302,
                303,
                307,
                308,
            }:
                if (
                    redirect_count
                    >= self.max_redirects
                ):
                    raise ArticleFetchError(
                        "Maksimum redirect "
                        "sayisi asildi."
                    )

                location = (
                    response.headers.get(
                        "location"
                    )
                )

                if not location:
                    raise ArticleFetchError(
                        "Redirect Location "
                        "header icermiyor."
                    )

                current_url = urljoin(
                    current_url,
                    location,
                )

                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ArticleFetchError(
                    "Makale HTTP hatasi "
                    f"dondurdu: "
                    f"{response.status_code}"
                ) from exc

            return (
                response,
                current_url,
            )

        raise ArticleFetchError(
            "Makale alinamadi."
        )

    def _read_limited(
        self,
        response: httpx.Response,
    ) -> bytes:
        content_length = (
            response.headers.get(
                "content-length"
            )
        )

        if content_length:
            try:
                if (
                    int(content_length)
                    > self.max_bytes
                ):
                    raise ArticleFetchError(
                        "Makale boyutu izin "
                        "verilen siniri asiyor."
                    )
            except ValueError:
                pass

        data = bytearray()

        for chunk in response.iter_bytes():
            data.extend(
                chunk
            )

            if (
                len(data)
                > self.max_bytes
            ):
                raise ArticleFetchError(
                    "Makale boyutu izin "
                    "verilen siniri asiyor."
                )

        return bytes(
            data
        )

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:
        return " ".join(
            value.split()
        ).strip()

    def _extract_content(
        self,
        html: str,
    ) -> tuple[
        str,
        str,
    ]:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        for tag_name in (
            "script",
            "style",
            "noscript",
            "svg",
            "form",
            "nav",
            "footer",
            "aside",
        ):
            for element in soup.find_all(
                tag_name
            ):
                element.decompose()

        title = ""

        if soup.title:
            title = self._normalize_text(
                soup.title.get_text(
                    " ",
                    strip=True,
                )
            )

        root = (
            soup.find("article")
            or soup.find("main")
            or soup.body
            or soup
        )

        paragraphs = [
            self._normalize_text(
                paragraph.get_text(
                    " ",
                    strip=True,
                )
            )
            for paragraph in root.find_all(
                ["p", "h1", "h2", "h3"]
            )
        ]

        content = "\n".join(
            paragraph
            for paragraph in paragraphs
            if paragraph
        ).strip()

        if len(content) < self.min_chars:
            fallback = (
                self._normalize_text(
                    root.get_text(
                        "\n",
                        strip=True,
                    )
                )
            )

            if len(fallback) > len(
                content
            ):
                content = fallback

        if len(content) < self.min_chars:
            raise ArticleFetchError(
                "Makale icerigi yeterince "
                "uzun degil."
            )

        return (
            title,
            content,
        )

    def fetch(
        self,
        url: str,
    ) -> ArticleDocument:
        response, final_url = (
            self._fetch_response(
                url
            )
        )

        content_type = (
            response.headers.get(
                "content-type",
                ""
            )
            .split(
                ";",
                1,
            )[0]
            .strip()
            .lower()
        )

        if content_type not in {
            "text/html",
            "application/xhtml+xml",
        }:
            raise ArticleFetchError(
                "Desteklenmeyen content-type: "
                f"{content_type or 'unknown'}"
            )

        raw = self._read_limited(
            response
        )

        encoding = (
            response.encoding
            or "utf-8"
        )

        html = raw.decode(
            encoding,
            errors="replace",
        )

        title, content = (
            self._extract_content(
                html
            )
        )

        return ArticleDocument(
            url=url,
            final_url=final_url,
            title=title,
            content=content,
            content_type=content_type,
        )
