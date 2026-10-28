import argparse
import getpass
import sys

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password, password_policy_errors
from app.core.validation import validate_username
from app.models.enums import NotificationKind, Role
from app.models.user import User
from app.repositories import notifications as notifications_repo
from app.repositories import users as users_repo


def _read_password(stdin: bool) -> str:
    if stdin:
        return sys.stdin.readline().rstrip("\n")
    if settings.admin_initial_password:
        return settings.admin_initial_password
    password = getpass.getpass("Нууц үг: ")
    confirm = getpass.getpass("Нууц үг давтах: ")
    if password != confirm:
        raise SystemExit("Нууц үг таарахгүй байна.")
    return password


def create_admin(args: argparse.Namespace) -> None:
    try:
        username = validate_username(args.username)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    password = _read_password(args.password_stdin)
    errors = password_policy_errors(password)
    if errors:
        raise SystemExit(" ".join(errors))

    with SessionLocal() as db:
        if users_repo.get_by_username(db, username) is not None:
            raise SystemExit("Энэ хэрэглэгчийн нэр аль хэдийн байна.")
        user = User(
            username=username,
            full_name=args.full_name.strip(),
            password_hash=hash_password(password),
            role=Role.ADMIN,
            is_active=True,
        )
        db.add(user)
        db.flush()
        notifications_repo.create(
            db,
            user_id=user.id,
            title="Администратор бүртгэл үүслээ",
            body="Системийн анхны администраторын бүртгэл амжилттай үүслээ.",
            kind=NotificationKind.SUCCESS,
        )
        db.commit()
        print(f"Администратор '{username}' амжилттай үүслээ (id={user.id}).")


def main() -> None:
    parser = argparse.ArgumentParser(description="People registry CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    admin = sub.add_parser("create-admin", help="Анхны администратор үүсгэх")
    admin.add_argument("--username", required=True)
    admin.add_argument("--full-name", required=True)
    admin.add_argument(
        "--password-stdin",
        action="store_true",
        help="Нууц үгийг stdin-ээс уншина (production/automation-д)",
    )
    admin.set_defaults(func=create_admin)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
