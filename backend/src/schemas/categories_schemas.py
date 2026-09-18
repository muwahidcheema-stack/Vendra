from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    rating: Decimal
    comment: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductListResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    description: str
    stock: int
    image_url: str | None = None
    is_active: bool
    category_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductDetailResponse(BaseModel):
    category: CategoryResponse
    reviews: list["ReviewResponse"] = []

    model_config = ConfigDict(from_attributes=True)

class PaginationProductResponse(BaseModel):
    items: list[ProductListResponse]
    total: int 
    page: int
    page_size: int
    pages: int

class CategoryBase(BaseModel):
    name: str
    slug: str
    img_url: str | None = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    img_url: str | None = None
