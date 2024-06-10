from uuid import UUID, uuid4
import bcrypt

from fastapi import Depends
from src.utils.database.session_injector import get_database

from src.services.user_service.models.user import User

def createUser(email: str, password: str) -> UUID:
    db: Session = next(get_database())
    user: User = User()

    user.id = uuid4()
    user.email = email
    
    print(password)
    salt = bcrypt.gensalt()
    user.password = bcrypt.hashpw(bytes(password, "utf-8"), salt) 

    db.add(user)
    db.commit()
    db.refresh(user)

    return user.id
