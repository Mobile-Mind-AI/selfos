from pydantic import BaseModel


class PresignRequest(BaseModel):
    ref_type: str
    ref_id: str
    filename: str
    mime: str | None = None


class PresignResponse(BaseModel):
    upload_url: str | None
    fields: dict
    preview_url: str | None

