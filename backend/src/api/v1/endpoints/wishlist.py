from fastapi import status, APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ....core.database import get_db
from ....core.dependencies import get_current_user
from ....models.models import WishList, User, Product
from ....schemas.wishlist_schemas import WishlistResponse, WishlistItemResponse

router = APIRouter(
    prefix="/wishlist",
    tags=["Wishlist"]
)

@router.get("", response_model=WishlistResponse)
async def get_user_wishlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(WishList).where(WishList.user_id == current_user.id).options(selectinload(WishList.product())).order_by(WishList.created_at.desc())
    )
    wishlist = (await db.execute(stmt)).scalars().all()
    if not wishlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist for this User Doesn't Wxist")
    return WishlistResponse(
        items= [WishlistItemResponse.model_validate(item) for item in wishlist],
        total_items=len(wishlist)
    )

@router.post("/{product_id}", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    prod_stmt = select(Product).where(Product.id == product_id, Product.is_active.is_(True))
    product = (await db.execute(prod_stmt)).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found or available")
    
    existing_stmt = select(WishList).where(WishList.user_id == current_user.id, WishList.product_id == product_id)
    existing_prod = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing_prod:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This Product is already in your Wishlist")

    new_item = WishList(user_id = current_user.id, product_id= product_id)
    db.add(new_item)
    await db.commit()

    refresh_stmt = select(WishList).where(WishList.id == new_item.id).options(selectinload(WishList.product))
    return (await db.execute(refresh_stmt)).scalar_one()
