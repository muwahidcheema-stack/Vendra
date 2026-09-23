from fastapi import APIRouter,Depends,HTTPException,status, Query
from decimal import Decimal
import math
# from sqlalchemy import select, asc,desc,or_, 
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ....models.models import Product,Review
from ....schemas.categories_schemas import ProductDetailResponse, ProductListResponse, PaginationProductResponse
from ....core.database import get_db

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.get("", response_model=PaginationProductResponse)
async def list_products(
    search: str | None = Query(None, description = "Search across name and description"),
    category_id: int | None = Query(None, description="Filter by category"),
    min_price: Decimal | None = Query(None, ge=0, description="Minimum price of products"),
    max_price: Decimal | None = Query(None, ge=0, description="Maximum price of products"),
    sort: str = Query("newest", pattern="^(newest|price_asc|price_desc)$"),
    page: int = Query(1, ge=0, description="Total Number of pages"),
    page_size: int = Query(12, ge=0, le=100, description="Products per Page"),
    is_active: bool | None = Query(None, description="Filter featured products"),
    db: AsyncSession = Depends(get_db)
):
    filters = [Product.is_active.is_(True)]

    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
            )
        )
    if category_id is not None:
        filters.append(Product.category_id == category_id)
    if min_price is not None:
        filters.append(Product.price >= min_price)
    if max_price is not None:
        filters.append(Product.price <= max_price)
    if is_active is not None:
        filters.append(Product.is_active.is_(is_active))

    # Total filters
    count_query = select(func.count(Product.id)).where(*filters)
    total_products = (await db.execute(count_query)).scalar() or 0

    # Base Query
    query = select(Product).where(*filters)

    # Sorting
    if sort == "price_asc":
        query = query.order_by(asc(Product.price))
    elif sort == "price_desc":
        query = query.order_by(desc(Product.price))
    else:
        query = query.order_by(desc(Product.created_at))

    # Offset and Limits
    offset_value = (page -1) * page_size
    query = query.offset(offset_value).limit(page_size)

    result = await db.execute(query)
    products = result.scalars().all()

    total_pages = math.ceil(total_products / page_size) if total_products > 0 else 0

    return PaginationProductResponse(
        items= [ProductListResponse.model_validate(p) for p in products],
        total=total_products,
        page=page,
        page_size=page_size,
        pages=total_pages
    )

@router.get("/{id}", response_model=ProductDetailResponse)
async def get_product_details(id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Product)
        .where(Product.id == id, Product.is_active.is_(True))
        .options(
            selectinload(Product.category),
            selectinload(Product.reviews)
        )
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product Details Not Found")

    return product