import time

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from passlib.exc import InvalidTokenError
from sqlalchemy import select
from starlette import status

from src.app import db_session
from src.app.exception_handlers import ErrorCodeResponse, ErrorInfoContainer
from src.app.models import AdminUser
from src.config.local_settings import JWT_SECRET_KEY
from src.config.settings import ACCESS_TOKEN_EXPIRE_TIME, JWT_ALGORITHM

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
reusable_oauth = OAuth2PasswordBearer(tokenUrl="/auth/login", scheme_name="JWT", auto_error=True)


def get_now_epoch():
    return int(time.time())


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def get_jwt_token(username: str) -> str:
    payload = {
        "username": username,
        "iat": get_now_epoch(),
        "exp": get_now_epoch() + ACCESS_TOKEN_EXPIRE_TIME,
    }
    encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_jwt_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
    except jwt.ExpiredSignatureError:
        raise ErrorCodeResponse(
            error=ErrorInfoContainer.token_expired,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    except jwt.PyJWTError:
        raise ErrorCodeResponse(
            error=ErrorInfoContainer.invalid_token,
            status_code=status.HTTP_403_FORBIDDEN,
        )
    except InvalidTokenError:
        raise ErrorCodeResponse(
            error=ErrorInfoContainer.invalid_token,
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return payload


async def get_current_user(token: str = Depends(reusable_oauth)):
    payload = decode_jwt_token(token)
    username: str = payload.get("username")
    try:
        with db_session() as session:
            admin_user = session.scalar(select(AdminUser).where(AdminUser.username == username))
            session.expunge(admin_user)
            return admin_user
    except Exception:
        raise ErrorCodeResponse(
            error=ErrorInfoContainer.invalid_token,
            status_code=status.HTTP_403_FORBIDDEN,
        )
