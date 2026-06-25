from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3

from security import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# ==========================
# Models
# ==========================

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ==========================
# Register
# ==========================

@router.post("/register")
def register_user(data: RegisterRequest):

    conn = sqlite3.connect("meeting.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (data.email,)
    )

    existing = cursor.fetchone()

    if existing:

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    cursor.execute(
        """
        INSERT INTO users(
            name,
            email,
            password
        )
        VALUES(?,?,?)
        """,
        (
            data.name,
            data.email,
            data.password
        )
    )

    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    token = create_access_token(
        {
            "user_id": user_id
        }
    )

    return {
        "access_token": token,
        "user": {
            "id": user_id,
            "name": data.name,
            "email": data.email
        },
        "message": "Registration successful"
    }


# ==========================
# Login
# ==========================

@router.post("/login")
def login_user(data: LoginRequest):

    conn = sqlite3.connect("meeting.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            email
        FROM users
        WHERE email=?
        AND password=?
        """,
        (
            data.email,
            data.password
        )
    )

    user = cursor.fetchone()

    conn.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {
            "user_id": user[0]
        }
    )

    return {
        "access_token": token,
        "user": {
            "id": user[0],
            "name": user[1],
            "email": user[2]
        }
    }