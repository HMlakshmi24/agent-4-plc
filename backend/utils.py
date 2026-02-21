# backend/utils.py
import os
import bcrypt
from datetime import datetime, timedelta
# from passlib.context import CryptContext
from jose import jwt, JWTError
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi import Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
# Removed Mongo DB import

# Load .env from parent directory
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey123")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    # return pwd_context.hash(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    # return pwd_context.verify(password, hashed)
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def send_welcome_email(to_email: str, username: str, password: str):
    subject = "Welcome to Agent4PLC 🎉"
    body = f"""
    Hi {username},

    Welcome to Agent4PLC! Your account has been created successfully.

    Username: {username}
    Password: {password}

    Please keep these details safe.

    Regards,
    Team Parijat !!
    """

    msg = MIMEText(body, "plain")
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")

def send_otp_email(to_email: str, username: str, otp: str):
    subject = "Reset Your Password - Automind AI"
    body = f"""
Hi {username},

Someone requested a new password for your Automind AI account.

Your password reset OTP is: {otp}

If you didn't make this request, just ignore this email.

Regards,
Team Automind !!
"""
    msg = MIMEText(body, "plain")
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
    except Exception as e:
        print(f"Error sending OTP email: {e}")


# ----------------------------
# Get current user from JWT
# ----------------------------
async def get_current_user(request: Request):
    """Dependency to get the currently logged-in user from JWT token"""
    auth: str = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    try:
        scheme, token = auth.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload invalid",
            )
        return {"sub": user_id, "email": email}
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
