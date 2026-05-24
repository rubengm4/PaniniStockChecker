from __future__ import annotations

import argparse
import logging
import sys

from src.runner import list_status, run_check, test_telegram


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Panini FIFA World Cup 2026 stock monitor (Spain)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check_parser = sub.add_parser("check", help="Run all configured stock checks")
    check_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check and update state without sending Telegram alerts",
    )

    sub.add_parser("list", help="Show watches and last known status")
    sub.add_parser("test-telegram", help="Send a test message to verify Telegram setup")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if args.command == "check":
        alerts = run_check(dry_run=args.dry_run)
        logging.info("Done. Alerts sent: %d", alerts)
        return 0

    if args.command == "list":
        list_status()
        return 0

    if args.command == "test-telegram":
        return 0 if test_telegram() else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
