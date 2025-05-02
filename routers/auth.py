from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from models.user import UserCreate, UserLogin, UserResponse
from database import get_user_collection
from utils.email import send_welcome_email
from main import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, pwd_context

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# SECRET_KEY = "my_secret_key"
# ALGORITHM = "HS256"


@router.post("/register")
async def register(user: UserCreate):
    users = await get_user_collection()

    # Check if user exists
    if await users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = pwd_context.hash(user.password)

    # Create user document
    user_doc = {
        "email": user.email,
        "name": user.name,
        "hashed_password": hashed_password,
        "role": "user",
        "created_at": datetime.utcnow()
    }

    # Insert user
    result = await users.insert_one(user_doc)

    # Send welcome email
    await send_welcome_email(user.email, user.name)

    return {"message": "User registered successfully"}


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = await get_user_collection()
    user = await users.find_one({"email": form_data.username})

    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": user["email"]})

    # Convert MongoDB _id to string id for Pydantic model
    user_dict = {**user, "id": str(user["_id"])}
    del user_dict["_id"]  # Remove the _id field

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user_dict)
    }


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    users = await get_user_collection()
    user = await users.find_one({"email": email})
    if user is None:
        raise credentials_exception

    # Convert MongoDB _id to string id for Pydantic model
    user_dict = {**user, "id": str(user["_id"])}
    del user_dict["_id"]  # Remove the _id field

    return UserResponse(**user_dict)