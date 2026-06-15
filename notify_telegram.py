#!/usr/bin/env python3
"""post_save_post hook: send the generated post to Telegram.

Reads creds from /data/.telegram (KEY=VALUE lines), post content from stdin.
Never fails the pipeline: any error is swallowed and exit code is 0.
NOTE: this file lives on the VPS /data volume (not in git), alongside .telegram.
"""
import sys
import urllib.parse
import urllib.request

CREDS = "/data/.telegram"
MAX = 4000  # Telegram hard limit is 4096 chars per message


def main() -> None:
    env = {}
    try:
        with open(CREDS) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
        token = env["TELEGRAM_BOT_TOKEN"]
        chat_id = env["TELEGRAM_CHAT_ID"]
    except Exception as e:
        print(f"telegram hook: cred error: {e}", file=sys.stderr)
        return

    post = sys.stdin.read().strip()
    if not post:
        return
    title = post.splitlines()[0].lstrip("# ").strip()
    body = f"📝 Novo post gerado\n\n{post}"

    try:
        data = urllib.parse.urlencode(
            {"chat_id": chat_id, "text": body[:MAX], "disable_web_page_preview": "true"}
        ).encode()
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{token}/sendMessage", data, timeout=15
        )
        print(f"telegram hook: sent '{title}'")
    except Exception as e:
        print(f"telegram hook: send failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
