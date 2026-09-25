import httpx
import pytest

from external.article_fetcher import (
    ArticleContentFetcher,
    ArticleFetchError,
    UnsafeArticleURLError,
    validate_public_http_url,
)


PUBLIC_IP = [
    "93.184.216.34"
]


def public_resolver(
    hostname: str,
):
    return PUBLIC_IP


def test_blocks_localhost():
    with pytest.raises(
        UnsafeArticleURLError
    ):
        validate_public_http_url(
            "http://localhost/admin"
        )


def test_blocks_private_ip():
    def private_resolver(
        hostname,
    ):
        return [
            "127.0.0.1"
        ]

    with pytest.raises(
        UnsafeArticleURLError
    ):
        validate_public_http_url(
            "https://example.test/",
            resolver=private_resolver,
        )


def test_fetcher_extracts_article_content():
    body = """
    <html>
      <head>
        <title>Test Haber</title>
      </head>
      <body>
        <nav>Menu</nav>
        <article>
          <h1>Test Haber Basligi</h1>
          <p>
            Bu paragraf haberin ana
            icerigini temsil etmektedir.
          </p>
          <p>
            Ikinci paragraf da yeterli
            metin uzunlugu saglar.
          </p>
        </article>
        <footer>Footer</footer>
      </body>
    </html>
    """

    def handler(
        request: httpx.Request,
    ):
        return httpx.Response(
            200,
            headers={
                "content-type":
                    "text/html; charset=utf-8"
            },
            text=body,
        )

    transport = httpx.MockTransport(
        handler
    )

    with httpx.Client(
        transport=transport
    ) as client:
        fetcher = ArticleContentFetcher(
            client=client,
            resolver=public_resolver,
            min_chars=30,
        )

        document = fetcher.fetch(
            "https://example.test/article"
        )

    assert (
        document.title
        == "Test Haber"
    )

    assert (
        "ana icerigini"
        in document.content
    )

    assert (
        "Menu"
        not in document.content
    )


def test_redirect_to_private_host_is_blocked():
    def resolver(
        hostname: str,
    ):
        if (
            hostname
            == "example.test"
        ):
            return PUBLIC_IP

        return [
            "127.0.0.1"
        ]

    def handler(
        request: httpx.Request,
    ):
        return httpx.Response(
            302,
            headers={
                "location":
                    "http://internal.test/private"
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with httpx.Client(
        transport=transport
    ) as client:
        fetcher = ArticleContentFetcher(
            client=client,
            resolver=resolver,
        )

        with pytest.raises(
            UnsafeArticleURLError
        ):
            fetcher.fetch(
                "https://example.test/start"
            )


def test_rejects_non_html_content():
    def handler(
        request: httpx.Request,
    ):
        return httpx.Response(
            200,
            headers={
                "content-type":
                    "application/pdf"
            },
            content=b"%PDF-test",
        )

    transport = httpx.MockTransport(
        handler
    )

    with httpx.Client(
        transport=transport
    ) as client:
        fetcher = ArticleContentFetcher(
            client=client,
            resolver=public_resolver,
        )

        with pytest.raises(
            ArticleFetchError
        ):
            fetcher.fetch(
                "https://example.test/file"
            )
