import time
import jwt

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from config import settings
from database import engine, SessionLocal
from models import Base, Token
import crud


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
        if crud.count_users(db) == 0:
            hashed = bcrypt.hash("secret")
            crud.create_user(db, username="admin", password_hash=hashed)
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
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@app.post("/login", response_model=Token, tags=["auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, form_data.username)
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
    existing = crud.get_user_by_username(db, username)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = bcrypt.hash(password)
    user = crud.create_user(db, username, hashed_pw)
    return {"id": user.id, "username": user.username}
