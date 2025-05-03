import time
import jwt

from fastapi import Depends, FastAPI, HTTPException, status, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from config import settings
from database import engine, SessionLocal
from models import Base, Token
import crud_no_cache
import crud_with_cache
from schemas import User as UserSchema

app = FastAPI(title="User service")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def init_data():
    db = SessionLocal()
    try:
        if crud_with_cache.count_users(db) == 0:
            hashed = bcrypt.hash("secret")
            crud_with_cache.create_user(db, username="admin", password_hash=hashed)
        db.commit()
    finally:
        db.close()


init_data()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_jwt_token(username: str) -> str:
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + 60 * 60,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    username = decode_jwt_token(token)
    user = crud_with_cache.get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@app.post("/login", response_model=Token, tags=["auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = crud_no_cache.get_user_by_username(db, form_data.username)
    if not user or not bcrypt.verify(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_jwt_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", tags=["users"])
async def read_current_user(current_user=Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}


@app.post("/users", tags=["users"])
async def create_new_user(
    username: str,
    password: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    existing = crud_with_cache.get_user_by_username(db, username)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = bcrypt.hash(password)
    user = crud_with_cache.create_user(db, username, hashed_pw)
    return {"id": user.id, "username": user.username}


@app.get("/users_no_cache/{user_id}", tags=["users"], response_model=UserSchema)
def read_user_nocache(
    user_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    user = crud_no_cache.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users_with_cache/{user_id}", tags=["users"], response_model=UserSchema)
def read_user_cached(
    user_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    user = crud_with_cache.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
