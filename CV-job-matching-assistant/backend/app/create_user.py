from __future__ import annotations

import argparse
import getpass

from backend.app.auth import create_user


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a HireReadyAI user")
    parser.add_argument("username")
    parser.add_argument("--role", choices=["admin", "user"], default="user")
    arguments = parser.parse_args()
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match")

    user = create_user(arguments.username, password, arguments.role)
    print(f"Created {user.role} user: {user.username}")


if __name__ == "__main__":
    main()
