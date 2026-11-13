import math
from fastapi import APIRouter, status, HTTPException, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.dependencies import require_admin
from ....models.models import OrderItem, Order, OrderStatus, User
from ....schemas.order_schemas import OrderItemResponse, OrderListResponse, PaginatedOrderResponse, OrderStatusUpdate, OrderResponse

router = APIRouter(
    prefix="/admin/orders",
    tags=["Admin Orders"]
)

@router.get("", response_model=PaginatedOrderResponse)
async def list_all_orders(
    status_filter: OrderStatus | None = Query(None, alias='status', description="Filter orders by status"),
    page: int = Query(1, ge=1, description="Page Number"),
    page_size: int = Query(10, ge=0, le=50, description="Items per page"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db) 
):
    filters = []
    if status_filter is not None:
        filters.append(Order.status == status_filter)

    cnt_stmt = select(func.count(Order.id)).where(*filters)
    total = (await db.execute(cnt_stmt)).scalar() or 0
    offset = (page - 1) * page_size
    stmt = (
        select(Order)
        .where(*filters)
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
            status=o.status.value if hasattr(o.status, "value") else str(o.status),
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

@router.patch("/{id}/status", response_model=OrderResponse)
async def update_order_status(
    id: int,
    status_in: OrderStatusUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Order)
        .where(Order.id == id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order Not Found")

    order.status = status_in.status
    await db.commit()
    await db.refresh(order)

    items_response = [
        OrderItemResponse(
            id = item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else "[Archived Product]",
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