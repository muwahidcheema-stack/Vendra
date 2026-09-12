from fastapi import HTTPException, status, APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.dependencies import get_current_user
from ....core.security import verify_password, get_password_hash, create_access_token
from ....models.models import User
from ....schemas.users import UserBase, UserCreate, UserResponse, UserUpdate, Token

router = APIRouter(
    prefix= '/auth',
    tags=['Authentication'],
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email == user_in.email)
    existing_user = (await db.execute(query)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this emial already exists")
    new_user = User(
        email= user_in.email,
        password = get_password_hash(user_in.password),
        full_name = user_in.full_name
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/login", response_model=Token)
async def login(form_data : OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    query = select(User).where(User.email == form_data.username)
    user = (await db.execute(query)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Login Credentials")
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token)

@router.put("/me", response_model=UserResponse)
async def update_cuurent_user(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data:
        return current_user
    stmt = (
        update(User).where(User.id == current_user.id).values(**update_data).returning(User)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()
