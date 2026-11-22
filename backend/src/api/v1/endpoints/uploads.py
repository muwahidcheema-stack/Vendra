import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile, Request
from ....models.models import User
from ....core.dependencies import require_admin
from ....schemas.upload_schemas import ImageUploadResponse

router = APIRouter(
    prefix="/admin",
    tags=["Admin Uploads"]
)

BASE_DIR = Path(__file__).resolve().parents[3]
UPLOAD_DIR = BASE_DIR / "static" / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


@router.post("/upload", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    admin: User = Depends(require_admin)
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No image found")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported File Type. Supported Types: jpg, jpeg, png, webp")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported File Content Type. Supported Types: image/jpeg, image/png, image/webp")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is Empty")

    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    destination_path = UPLOAD_DIR/unique_filename

    with open(destination_path, "wb") as buffer:
        buffer.write(contents)

    relative_path = f"/static/uploads/{unique_filename}"
    base_url = str(request.base_url).rstrip("/")
    full_url = f"{base_url}{relative_path}"

    return ImageUploadResponse(
        filename=unique_filename,
        relative_path=relative_path,
        url=full_url,
    )
                
    