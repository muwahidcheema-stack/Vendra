from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

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

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(..., ge=0)
    stock: int = Field(default=0, ge=0)
    image_url: str | None = None
    is_active: bool = True
    category_id: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=0, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(None, ge=0)
    stock: int | None = Field(None, ge=0)
    image_url: str | None = None
    is_active: bool | None = None
    category_id: int | None = None
    
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

class ProductDetailResponse(ProductListResponse):
    category: CategoryResponse
    # reviews: list["ReviewResponse"] = []

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