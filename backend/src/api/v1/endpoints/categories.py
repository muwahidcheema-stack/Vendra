from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.dependencies import get_current_user, require_admin
from ....models.models import Category, User
from ....schemas.categories_schemas import CategoryResponse, CategoryCreate, CategoryUpdate

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

@router.get("", response_model=list[CategoryResponse])
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    query = select(Category).order_by(Category.name.asc())
    result = await db.execute(query)
    return result.scalars().all()

@router.post("", response_model=CategoryCreate, status_code=status.HTTP_201_CREATED)
async def create_category (
    category_in: CategoryCreate, 
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Category).where(Category.slug == category_in.slug)
    existing = (await db.execute(query)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this slug already exists")
    category = Category(
        name = category_in.name,
        slug = category_in.slug,
        image_url = category_in.img_url,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Category).where(Category.id == category_id)
    category = (await db.execute(query)).scalar_one_or_none()
    if not category:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="Category with this Id doesn't exist")
    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(Category).where(Category.id == category_id)
    category = (await db.execute(query)).scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category with this Id doesn't exist")
    await db.delete(category)
    await db.commit()
    return {"Message": "Successfully Deleted Category"}