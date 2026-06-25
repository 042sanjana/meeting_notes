from datetime import datetime, timedelta

from jose import JWTError, jwt

from fastapi import (
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

import sqlite3


SECRET_KEY = "my_super_secret_key_12345"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


security = HTTPBearer()


# ==========================
# Create JWT Token
# ==========================

def create_access_token(
    data: dict
):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {"exp": expire}
    )

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# ==========================
# Verify JWT Token
# ==========================

def get_current_user(
    credentials:
    HTTPAuthorizationCredentials =
    Depends(security)
):

    try:

        token =credentials.credentials

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id =payload.get("user_id")

        if user_id is None:

            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        conn = sqlite3.connect(
            "meeting.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                name,
                email
            FROM users
            WHERE id=?
            """,
            (user_id,)
        )

        user =cursor.fetchone()

        conn.close()

        if not user:

            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        return {
            "id": user[0],
            "name": user[1],
            "email": user[2]
        }

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )