from decimal import Decimal
from fastapi import HTTPException,APIRouter,status, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.database import get_db
from ....core.dependencies import get_current_user
from ....models.models import User, CartItem, Product
from ....schemas.cart_schemas import CartItemResponse, CartProductResponse, CartItemBase, CartItemCreate, CartItemUpdate, CartResponse

router = APIRouter(
    tags= "Cart",
    prefix=['cart']
)

async def build_cart_response(user_id: int, db: AsyncSession) -> CartResponse:
    stmt = (
        select(CartItem).where(CartItem.user_id == user_id).options(select(CartItem.product)).order_by(CartItem.id.asc())
    )
    result = (await db.execute(stmt))
    cart_items = result.scalars().all()

    formatted_items: list[CartItemResponse] = []
    total_price  = Decimal("0.0")
    total_items = 0

    for item in cart_items:
        subtotal = Decimal(str(item.product.price)) * item.quantity
        total_price += subtotal
        total_items += item.quantity

        formatted_items.append(
            CartItemResponse(
                id = item.id,
                product_id = item.product_id,
                quantity = item.quantity,
                created_at = item.created_at,
                product = item.product,
                subtotal = subtotal,
            )
        )
    return CartResponse(
        items = formatted_items,
        total_items = total_items,
        total_price = total_price
    )

@router.get("", response_model=CartResponse)
async def get_user_cart(    
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await build_cart_response(current_user.id, db)

@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    item_in: CartItemCreate,
    current_user: User = Depends(get_db),
    db: AsyncSession = Depends(get_current_user)
):
    product_stmt = select(Product).where(Product.id == item_in.id)
    product = (await db.execute(product_stmt)).scalar_one_or_none()
    if not product or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This product is not available")
    stmt = (
        select(CartItem).where(CartItem.user_id == current_user.id, CartItem.product_id == item_in.product_id)
    )
    cart_item = (await db.execute(stmt)).scalar_one_or_none()
    target_quantity = item_in.quantity if not cart_item else cart_item.quantity + item_in.quantity 
    if product.stock <  target_quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested Quantity Can't be fulfilled")
    if cart_item:
        cart_item.quantity =  target_quantity
    else:
        new_item = CartItem(
            user_id=current_user.id,
            product_id= item_in.product_id,
            quantity= item_in.quantity
        )
        db.add(new_item)
    await db.commit()
    return build_cart_response(current_user.id, db)

# @router.put("/items/{item_id}" , response_model=CartResponse)
