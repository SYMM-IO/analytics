from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import get_db_session
from app.exception_handlers import ErrorCodeResponse, ErrorInfoContainer
from app.models import AdminUser
from app.response_models import Login, ReadMe
from utils.security_utils import (
    get_jwt_token,
    get_current_user,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Login)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: Session = Depends(get_db_session),
):
    user = session.scalar(select(AdminUser).where(AdminUser.username == form_data.username))
    if not user or not verify_password(form_data.password, user.password):
        raise ErrorCodeResponse(
            error=ErrorInfoContainer.incorrect_username_password,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return {"access_token": get_jwt_token(user.username)}


@router.get("/me", response_model=ReadMe)
async def read_me(current_user: Annotated[AdminUser, Depends(get_current_user)]):
    return {
        "username": current_user.username,
        "createTimestamp": current_user.createTimestamp,
    }
