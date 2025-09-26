from fastapi import APIRouter, Depends

from ..deps import get_current_user_id
from ..schemas.attachments import PresignRequest, PresignResponse


router = APIRouter(prefix="/attachments")


@router.post("/presign", response_model=PresignResponse)
def presign_upload(_: str = Depends(get_current_user_id), payload: PresignRequest = None):  # type: ignore[assignment]
    # Заглушка: возвращаем структуру без реальной подписи
    return PresignResponse(upload_url=None, fields={}, preview_url=None)

