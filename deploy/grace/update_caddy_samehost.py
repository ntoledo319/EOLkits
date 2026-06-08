#!/usr/bin/env python3
"""Install same-host EOLkits API routing into the live Caddyfile.

This keeps the existing static `eolkits.com` site and routes only API paths to
the `eolkits-api` compose service on localhost:8120. It also removes the earlier
experimental `api.eolkits.com` fenced block if present, so DNS is not required.
"""

from pathlib import Path


CADDYFILE = Path("/etc/caddy/Caddyfile")

OLD_STATIC_BLOCK = """eolkits.com, www.eolkits.com {
    encode zstd gzip
    root * /var/www/eolkits
    file_server
}
"""

NEW_SAME_HOST_BLOCK = """eolkits.com, www.eolkits.com {
    encode zstd gzip

    @eolkitsApi path /health /api/* /upload/* /webhook/* /pack/install /pack/setup /support/* /partners/signup /partners/verify/* /partners/*/audit
    handle @eolkitsApi {
        reverse_proxy 127.0.0.1:8120
    }

    handle {
        root * /var/www/eolkits
        file_server
    }
}
"""


def remove_fenced_api_subdomain_block(text: str) -> str:
    begin = "# >>> eolkits-api >>>"
    end = "# <<< eolkits-api <<<"
    if begin not in text or end not in text:
        return text
    head, _, rest = text.partition(begin)
    _, _, tail = rest.partition(end)
    return head.rstrip() + "\n\n" + tail.lstrip("\n")


def main() -> int:
    text = CADDYFILE.read_text()
    text = remove_fenced_api_subdomain_block(text)
    if NEW_SAME_HOST_BLOCK in text:
        CADDYFILE.write_text(text)
        return 0
    if OLD_STATIC_BLOCK not in text:
        start = text.find("eolkits.com, www.eolkits.com {")
        if start == -1:
            raise SystemExit("expected eolkits.com block not found")
        depth = 0
        end = None
        for idx in range(start, len(text)):
            char = text[idx]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break
        if end is None:
            raise SystemExit("unterminated eolkits.com block")
        text = text[:start] + NEW_SAME_HOST_BLOCK.rstrip() + text[end:]
        CADDYFILE.write_text(text)
        return 0
    CADDYFILE.write_text(text.replace(OLD_STATIC_BLOCK, NEW_SAME_HOST_BLOCK, 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

