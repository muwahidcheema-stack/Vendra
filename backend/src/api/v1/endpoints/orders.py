import math
from fastapi import HTTPException, status, Query, Depends, APIRouter
from sqlalchemy import func, select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.dependencies import get_current_user
from ....models.models import User, OrderItem, Order
from ....schemas.order_schemas import OrderCreate, OrderItemResponse, OrderListResponse, OrderResponse, PaginatedOrderResponse
from ....services.order_service import create_order_transaction

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await create_order_transaction(
        user=current_user,
        order_in=order_in,
        session=db,
    )

    items_response = [
        OrderItemResponse(
            id = item.id,
            product_id=item.product_id,
            product_name=item.product.name,
            quantity=item.quantity,
            unit_pirce=item.price,
            sub_total=item.price * item.quantity,
        )
        for item in order.items
    ]

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        payment_method=order.payment_method,
        shipping_address=order.shipping_address,
        created_at=order.created_at,
        items=items_response,
    )

@router.get("/me", response_model=PaginatedOrderResponse)
async def list_my_orders(
    page: int = Query(1, ge=1, description="Page Number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db), 
):
    count_stmt = select(func.count(Order.id)).where(Order.user_id == current_user.id)
    total = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * page_size

    stmt = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .options(selectinload(Order.items))
        .order_by(desc(Order.created_at))
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(stmt)
    orders = result.scalars().all()

    items = [
        OrderListResponse(
            id=o.id,
            total_amount=o.total_amount,
            status=o.status,
            payment_method=o.payment_method,
            created_at=o.created_at,
            items_count=sum(i.quantity for i in o.items),
        )
        for o in orders
    ]

    total_pages = math.ceil(total/page_size) if total > 0 else 1

    return PaginatedOrderResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages,
    )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_detail(
    order_id : int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items)
        .selectinload(OrderItem.product))
    )
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not Found")
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden for this order")

    items_response = [
        OrderItemResponse(
            id = item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else "Archived Product",
            quantity=item.quantity,
            unit_pirce=item.price,
            sub_total=item.price * item.quantity,
        )
        for item in order.items
    ]

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        payment_method=order.payment_method,
        shipping_address=order.shipping_address,
        created_at=order.created_at,
        items=items_response,
    )