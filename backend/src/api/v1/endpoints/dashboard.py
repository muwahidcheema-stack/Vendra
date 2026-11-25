from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from ....schemas.dashboard_schemas import AdminDashboardResponse, LowStockProduct, OrderStatusCount
from ....models.models import User, Product, Order, OrderStatus
from ....core.database import get_db
from ....core.dependencies import require_admin

router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"]
)

@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    min_stock: int = Query(5, ge=1, description="Stock Threshild for Less Stock Products"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rev_stmt = select(func.coalesce(func.sum(Order.total_amount),0)).where(Order.status != OrderStatus.CANCELLED)
    revenue = Decimal(str((await db.execute(rev_stmt)).scalar() or 0))

    order_cnt_stmt = select(func.count(Order.id))
    orders = (await db.execute(order_cnt_stmt)).scalar() or 0

    cnt_by_status_stmt = select(Order.status, func.count(Order.id)).group_by(Order.status)
    status_row = (await db.execute(cnt_by_status_stmt)).all()

    status_counts = {
        (row[0].value if hasattr(row[0], "value") else str(row[0])).lower() : row[1]
        for row in status_row
    }

    orders_by_status = OrderStatusCount(
        pending=status_counts.get("pending", 0),
        processing=status_counts.get("processing", 0),
        confirmed=status_counts.get("confirmed", 0),
        delivered=status_counts.get("delivered", 0),
        shipped=status_counts.get("shipped", 0),
        cancelled=status_counts.get("cancelled", 0),
    )

    active_stmt = select(func.count(Product.id)).where(Product.is_active.is_(True))
    active_products = (await db.execute(active_stmt)).scalar() or 0

    user_stmt = select(func.count(User.id))
    user_count = (await db.execute(user_stmt)).scalar() or 0

    low_stock_stmt = select(Product).where(Product.is_active.is_(True), Product.stock < min_stock).order_by(Product.stock.asc()).limit(10)
    low_stock_items = (await db.execute(low_stock_stmt)).scalars().all()

    return AdminDashboardResponse(
        total_revenue=revenue,
        total_orders=orders,
        total_products=active_products,
        total_users=user_count,
        orders_by_status=orders_by_status,
        low_stock_products=[LowStockProduct.model_validate(p) for p in low_stock_items]
    )