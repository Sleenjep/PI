from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
import time
from fastapi.middleware.cors import CORSMiddleware

SECRET_KEY = "SUPER_SECRET_KEY"
ALGORITHM = "HS256"

app = FastAPI(title="User Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fake_users_db = {"admin": "secret"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str


def create_jwt_token(username: str) -> str:
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + 60 * 60,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    username = decode_jwt_token(token)
    if username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found in fake DB"
        )
    return username


@app.post("/login", response_model=Token, tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password
    if username not in fake_users_db or fake_users_db[username] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_jwt_token(username)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", tags=["users"])
async def read_current_user(username: str = Depends(get_current_user)):
    return {"username": username}


@app.post("/users", tags=["users"])
async def create_new_user(
    user_data: UserCreate, current_user: str = Depends(get_current_user)
):
    if user_data.username in fake_users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    fake_users_db[user_data.username] = user_data.password
    return {"message": f"User '{user_data.username}' created successfully!"}
