from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.exception_handlers import ExceptionHandlers, ErrorCodeResponse
from config.settings import (
    SERVER_PORT,
)
from routers.auth_router import router as auth_router
from routers.snapshot_router import router as snapshot_router
from security.security_utils import get_current_user


# telegram_user_client: Client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # global telegram_user_client
    # telegram_user_client = await setup_telegram_client()
    # await telegram_user_client.start()
    yield
    # await telegram_user_client.stop()


app = FastAPI(
    lifespan=lifespan,
    title="Symmio analytics",
)
app.add_exception_handler(Exception, ExceptionHandlers.unhandled_exception)
app.add_exception_handler(HTTPException, ExceptionHandlers.http_exception)
app.add_exception_handler(ErrorCodeResponse, ExceptionHandlers.error_code_response)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(snapshot_router, dependencies=(Depends(get_current_user),))
app.include_router(auth_router)


@app.get("/")
def read_root( ):
    return { "Hello": "World" }


if __name__ == "__main__":
    uvicorn.run(app, port=SERVER_PORT)
