from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.dependencies import get_current_user
from ....models.models import Category
from ....schemas.categories_schemas import CategoryResponse

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

@router.get("", response_model=list[CategoryResponse])
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    query = select(Category).order_by(Category.name.asc())
    result = await db.execute(query)
    return result.scalars().all()
