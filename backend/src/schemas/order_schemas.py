from datetime import datetime
from pydantic import ConfigDict, BaseModel, Field
from decimal import Decimal

class OrderItemResponse(BaseModel):
    id: int
    product_id: int | None = None
    product_name: str | None = None
    quantity: int
    unit_pirce: Decimal
    sub_total: Decimal

    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    shipping_address: str = Field(..., min_length=0, max_length=500)
    payment_method: str = Field(default="COD", pattern="^(COD|STRIPE)$")

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: Decimal
    status: str
    payment_method: str
    shipping_address: str
    created_at: datetime
    items: list[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

class OrderListResponse(BaseModel):
    id: int
    total_amount: Decimal
    status: str
    payment_method: str
    created_at: datetime
    items_count: int

    model_config = ConfigDict(from_attributes=True)

class PaginatedOrderResponse(BaseModel):
    items: list[OrderListResponse]
    total: int
    page: int
    page_size: int
    pages: int