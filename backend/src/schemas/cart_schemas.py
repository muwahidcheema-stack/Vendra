from decimal import Decimal
from datetime import datetime
from pydantic import Field, BaseModel, ConfigDict

class CartProductResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    image_url:  str | None = None
    stock: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class CartItemBase(BaseModel):
    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")

class CartItemCreate(CartItemBase):
    product_id: int
    pass

class CartItemUpdate(CartItemBase):
    pass 

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    created_at: datetime
    product: CartProductResponse
    subtotal: int

    model_config = ConfigDict(from_attributes=True)

class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total_items: int
    total_price: Decimal