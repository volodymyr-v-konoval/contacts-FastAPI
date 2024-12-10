"""
Module for handling authetication, email varification, and token processing.

This module includes functions for token generation, password management,
user verification, and Cloudinary integration.
"""

import smtplib
import cloudinary 
import cloudinary.uploader

from decouple import config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import Depends, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database import get_db
from models import User

# Password context confifuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")

SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int)
REFRESH_TOKEN_EXPIRE_DAYS = config("REFRESH_TOKEN_EXPIRE_DAYS", cast=int)

SMTP_EMAIL = config("SMTP_EMAIL")
SMTP_PASSWORD = config("SMTP_PASSWORD")

cloudinary.config(
    cloud_name=config("CLOUDINARY_CLOUD_NAME"),
    api_key=config("CLOUDINARY_API_KEY"),
    api_secret=config("CLOUDINARY_API_SECRET")
)


def hash_password(password: str) -> str:
    """
    Hashes a password for storing in the database.
    
    Args:
        password (str): The plaintext password.
        
    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if a plaintext password matches its hashed version.
    
    Args:
        plain_password (str): The plaintext password.
        hashed_password (str): The hashed password.
        
    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Generates an access token for authentication.
    
    Args:
        data (dict): The data to encode in the token.
        
    Returns:
        str: The generated access token.
    """
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Generates a refresh token for renewing the access token.
    
    Args:
        data (dict): The data to encode in the token.
        
    Returns:
        str: The generated refresh token.
    """
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """
    Verifies the validity of a JWT token.
    
    Args:
        token (str): The JWT token.
        
    Returns:
        dict: The data encoded in the token.
        
    Raises:
        HTTPException: If the token is invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)):
    """
    Retrieves the currently authenticated user.
    
    Args:
        token (str): The JWT token provided by the client.
        db (Session): The database session.
        
    Returns:
        User: The user object.
        
    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """
    payload = verify_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return user


def send_verification_email(email: str, token: str):
    """
    Sends an email verificaion message.
    
    Args:
        email (str): The recipient's email address.
        token (str): The verification token.
        
    Raises:
        smtplib.SMTPException: If there is an issue sending the email.
    """
    sender_email = config("SMTP_EMAIL")
    sender_password = config("SMTP_PASSWORD")
    subject = "Verify your email"
    verification_link = f"http://localhost:8000/verify-email?token={token}"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = subject

    body = f"Click the link to verify your email: {verification_link}"
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
