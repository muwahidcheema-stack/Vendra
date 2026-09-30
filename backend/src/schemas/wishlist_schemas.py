from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal

class WishlistProductResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    image_url: str
    stock: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class WishlistItemResponse(BaseModel):
    id: int
    product_id: int
    created_at: datetime
    product: WishlistProductResponse

    model_config = ConfigDict(from_attributes=True)

class WishlistResponse(BaseModel):
    items: list[WishlistItemResponse]
    total_items: int