from uuid import UUID, uuid4
import bcrypt
from sqlalchemy.orm import Session

from utils.database.session_injector import get_database
from services.user_service.models.user import User


def create_user(email: str, password: str) -> UUID:
    db: Session = next(get_database())
    user: User = User()

    user.id = uuid4()
    user.email = email

    user.password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    db.add(user)
    db.commit()
    db.refresh(user)

    return user.id
