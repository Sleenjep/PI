import json
from typing import Optional
from sqlalchemy.orm import Session
from redis_utils import get_redis
from config import settings
from models import User

TTL = settings.redis_ttl


def _key_uid(uid: int) -> str:
    return f"user:{uid}"


def _key_uname(name: str) -> str:
    return f"user_by_name:{name}"


def _dump(user: User) -> str:
    return json.dumps(
        {"id": user.id, "username": user.username, "password_hash": user.password_hash}
    )


def _load(payload: str) -> User:
    data = json.loads(payload)
    return User(
        id=data["id"], username=data["username"], password_hash=data["password_hash"]
    )


def create_user(db: Session, username: str, password_hash: str) -> User:
    user = User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)

    r = get_redis()
    payload = _dump(user)
    r.set(_key_uid(user.id), payload, ex=TTL)
    r.set(_key_uname(user.username), payload, ex=TTL)

    return user


def get_user(db: Session, user_id: int) -> Optional[User]:
    r = get_redis()
    cached = r.get(_key_uid(user_id))
    if cached:
        return _load(cached)

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        r.set(_key_uid(user.id), _dump(user), ex=TTL)
        r.set(_key_uname(user.username), _dump(user), ex=TTL)
    return user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    r = get_redis()
    cached = r.get(_key_uname(username))
    if cached:
        return _load(cached)

    user = db.query(User).filter(User.username == username).first()
    if user:
        r.set(_key_uid(user.id), _dump(user), ex=TTL)
        r.set(_key_uname(user.username), _dump(user), ex=TTL)
    return user


def update_user_password(
    db: Session, user_id: int, new_password_hash: str
) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.password_hash = new_password_hash
    db.commit()
    db.refresh(user)

    r = get_redis()
    payload = _dump(user)
    pipe = r.pipeline()
    pipe.set(_key_uid(user.id), payload, ex=TTL)
    pipe.set(_key_uname(user.username), payload, ex=TTL)
    pipe.execute()

    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    db.delete(user)
    db.commit()

    r = get_redis()
    pipe = r.pipeline()
    pipe.delete(_key_uid(user_id))
    pipe.delete(_key_uname(user.username))
    pipe.execute()

    return True


def count_users(db: Session) -> int:
    return db.query(User).count()
