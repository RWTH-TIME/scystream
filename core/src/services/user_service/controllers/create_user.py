from uuid import UUID, uuid4
import bcrypt

from src.utils.database.session_injector import get_database
from src.services.user_service.models.user import User


def createUser(email: str, password: str) -> UUID:
    db: Session = next(get_database())
    user: User = User()

    user.id = uuid4()
    user.email = email
    
    user.password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()) 

    db.add(user)
    db.commit()
    db.refresh(user)

    return user.id 
