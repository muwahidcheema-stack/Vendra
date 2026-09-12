from fastapi import APIRouter,Depends,HTTPException,status, Query
from decimal import Decimal
import math
from sqlalchemy import select, asc,desc,or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ....models.models import Product,Review
from ....schemas.categories_schemas import ProductDetailResponse, ProductListResponse, PaginationProductResponse
from ....core.database import get_db

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

# @router.get("", response_model=PaginationProductResponse)
# async def list_products(
#     search: str | None = Query(None, description = "Search across name and description"),
#     category_id: id | None = Query(None, description="Filter by category"),
#     is_active: bool | None = Query(None, description="Filter featured products"),
#     db: AsyncSession = Depends(get_db)
# ):
#     return