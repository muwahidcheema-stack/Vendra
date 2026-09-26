from fastapi import APIRouter,Depends,HTTPException,status, Query
from decimal import Decimal
import math 
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ....models.models import Product,Review, User, Category
from ....schemas.categories_schemas import ProductDetailResponse, ProductListResponse, PaginationProductResponse, ProductCreate, ProductUpdate
from ....core.database import get_db
from ....core.dependencies import require_admin

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

@router.post("", response_model=ProductDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    catg_query = select(Category).where(Category.id == product_in.category_id)
    category = (await db.execute(catg_query)).scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with this ID {product_in.category_id} doesn't exist")
    new_product = Product(**product_in.model_dump())
    db.add(new_product)
    await db.commit()

    stmt = (
        select(Product).where(Product.id == new_product.id).options(selectinload(Product.category),selectinload(Product.reviews))
    )
    product = (await db.execute(stmt)).scalar_one()
    return product

@router.put("/{id}", response_model=ProductDetailResponse)
async def update_product(
    id: int,
    product_in: ProductUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Product).where(Product.id == id).options(selectinload(Product.category))
    )
    product = (await db.execute(stmt)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with this Id {product_in.category_id} was not found")
    update_date = product_in.model_dump(exclude_unset=True)

    if "category_id" in update_date:
        cat_query = select(Category).where(Category.id == update_date["category_id"])
        cat_stmt = (await db.execute(cat_query)).scalar_one_or_none()
        if not cat_stmt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"This Category Id {update_date['category_id']} was not found")
    for field, value in update_date.items():
        setattr(product,field,value)
    await db.commit()
    await db.refresh(product)

    stmt =(
        select(Product).where(Product.id == id).options(selectinload(Product.category))
    )
    return (await db.execute(stmt)).scalar_one()

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(Product).where(Product.id == id)
    product = (await db.execute(query)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with Id {id} is not found")
    product.is_active = False
    await db.commit()
    return None