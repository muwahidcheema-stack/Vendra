from pydantic import BaseModel

class ImageUploadResponse(BaseModel):
    filename: str
    relative_path: str
    url: str
    