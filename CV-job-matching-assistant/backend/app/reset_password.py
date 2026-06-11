from __future__ import annotations

import argparse
import getpass

from backend.app.auth import reset_user_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset a HireReadyAI user's password")
    parser.add_argument("username")
    arguments = parser.parse_args()
    password = getpass.getpass("New password: ")
    confirmation = getpass.getpass("Confirm new password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match")

    try:
        reset_user_password(arguments.username, password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Password reset for {arguments.username}. Existing sessions were invalidated.")


if __name__ == "__main__":
    main()
