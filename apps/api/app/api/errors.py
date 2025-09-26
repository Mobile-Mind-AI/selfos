from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str
    details: dict | None = None


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError):
        return JSONResponse(status_code=400, content=ApiError(code="bad_request", message=str(exc)).model_dump())

