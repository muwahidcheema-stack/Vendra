from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from sqlalchemy import delete, select

from ..models.models import CartItem, User, Order, OrderItem, OrderStatus, Product
from ..schemas.order_schemas import OrderCreate

async def create_order_transaction(
    user: User,
    order_in: OrderCreate,
    session: AsyncSession
) -> Order:
    async with session.begin():
        cart_stmt = (
            select(CartItem).where(CartItem.user_id == user.id).order_by(CartItem.id.asc())
        )
        cart_result = await session.execute(cart_stmt)
        cart_item = cart_result.scalars().all()
        if not cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart is empty")

        total_amount = Decimal("0.00")
        order_items_to_create: list[OrderItem] = []

        for item in cart_item:
            prod_stmt = (
                select(Product).where(Product.id == item.product_id).with_for_update()
            )
            prod_result = await session.execute(prod_stmt)
            product = prod_result.scalar_one_or_none()
            if not product or not product.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This Product is not longer available.")
            if product.stock < item.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Out of Stock")
            product.stock -= item.quantity
            unit_price = Decimal(str(product.price))
            item_total = item.quantity * unit_price
            total_amount += item_total

            order_items_to_create.append(
                OrderItem(
                    product_id = product.id,
                    quantity = item.quantity,
                    price = unit_price,
                )
            )
        new_order = Order(
            user_id= user.id,
            total_amount = total_amount,
            status= OrderStatus.PENDING,
            payment_method= order_in.payment_method,
            shipping_address = order_in.shipping_address,
            items = order_items_to_create,
        )
        session.add(new_order)

        clear_cart_stmt = (
            delete(CartItem).where(CartItem.user_id == user.id)
        )
        await session.execute(clear_cart_stmt)

    stmt = (
        select(Order).where(Order.id == new_order.id).options(
            selectinload(Order.items).selectinload(OrderItem.product)
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one()

async def cancel_order_transaction(
    order_id: int,
    user: User,
    session: AsyncSession,
) -> Order:
    async with session.begin():
        order_stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
            .with_for_update()
        )
        result = await session.execute(order_stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not Found")
        if order.user_id != user.id and user.role != 'admin':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Forbidden")

        cancelable_statuses = {OrderStatus.PENDING, OrderStatus.CONFIRMED}
        if order.status not in cancelable_statuses:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order can't be cancelled in PENDING or CONFIRMED state.")

        for item in order.items:
            if item.product_id is None:
                continue
            prod_stmt = (
                select(Product).where(Product.id == item.product_id).with_for_update()
            )
            product = (await session.execute(prod_stmt)).scalar_one_or_none()
            if product:
                product.stock += item.quantity
        order.status = OrderStatus.CANCELLED

    final_stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    return (await session.execute(final_stmt)).scalar_one()