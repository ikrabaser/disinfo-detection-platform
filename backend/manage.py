#!/usr/bin/env python
"""Django'nun komut satırı yönetim aracı (management CLI entrypoint)."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django import edilemedi. Sanal ortamınızı aktifleştirdiğinizden ve "
            "requirements.txt dosyasını yüklediğinizden emin olun."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
