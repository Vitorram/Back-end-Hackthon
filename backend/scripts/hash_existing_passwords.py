from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.security import hash_password
from backend.database.database import SessionLocal
from backend.models.usuario import Usuario

BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def main() -> None:
    db = SessionLocal()
    try:
        updated = 0
        users = db.query(Usuario).all()
        for user in users:
            current_password_value = user.senha_hash or ""
            if current_password_value.startswith(BCRYPT_PREFIXES):
                continue

            user.senha_hash = hash_password(current_password_value)
            updated += 1

        db.commit()
        print(f"Senhas convertidas para bcrypt: {updated}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
