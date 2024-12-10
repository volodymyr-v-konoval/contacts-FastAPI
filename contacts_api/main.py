import cloudinary

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import FastAPI, Depends, HTTPException, Query, Request, File, UploadFile
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from functools import partial
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from auth import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user, send_verification_email, verify_token
from database import engine, get_db
from models import Base, Contact, User
from schemas import ContactCreate, UserCreate, UserResponse, Token
from schemas import Contact as ContactResponse
Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=partial(lambda request: get_current_user().id), default_limits=["5/minute"])
app = FastAPI()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://your-domain.com"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Checking exception for limiter
@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Handles requests exceeding the rate limit.
    
    Args:
        request (Request): The HTTP request object.
        exc (RateLimitExceeded): The exception raised when the rate limit is exceeded.
        
    Returns:
        JSONResponse: A response with a 429 status code and an error message.
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded, please try again later."},
    )


@app.post("/users/avatar/")
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a user's avatar to Cloudinary and updates the user's avatar URL in the database.
    
    Args:
        file (UploadFile): The uploaded file object.
        db (Session): The database session.
        current_user (User): The currently authenticated user.

    Returns:
        dict: A dictionary containing the new avatar URL.

    Raises:
        HTTPException: If an error occurs during the upload process.
    """
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="avatars",
            public_id=f"user_{current_user.id}",
            overwrite=True,
            resource_type="image"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error uploading avatar")
    
    current_user.avatar_url = result.get("secure_url")
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {"avatar_url": current_user.avatar_url}

# Get all contacts
@app.get("/contacts/", response_model=List[ContactResponse])
def read_contacts(skip: int = 0, 
                  limit: int = 100, 
                  db: Session = Depends(get_db)):
    """
    Retrieves a list of contacts with optional pagination.
    
    Args:
        skip (int): The number of records to skip. Defaults to 0.
        limit (int): The maximum number of records to retrieve. Defaults to 100.
        db (Session): The datavase session.
        
    Returns:
        List[Contact]: A list of contact objects.
    """
    contacts = db.query(Contact).offset(skip).limit(limit).all()
    return contacts


# Get a single contact by ID
@app.get("/contacts/{contact_id}", response_model=ContactResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a contact by its ID.
    
    Args:
        contact_id (int): The ID of the contact.
        db (Session): The database session.
        
    Returns:
        Contact: The requested contact object.
        
    Raises:
        HTTPException: If the contact is not found.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact


# Update a contact
@app.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, 
                   contact: ContactCreate, 
                   db: Session = Depends(get_db)):
    """
    Updates a contact's information.
    
    Args:
        contact_id (int): The ID of the contact to update.
        contact (ContactCreate): The updated contact data.
        db (Session): The datavase session.
        
    Returns:
        Contact: The updated contact object.
        
    Raises:
        HTTPException: If the contact is not found.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    for var, value in vars(contact).items():
        setattr(db_contact, var, value) if value else None
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact
    

# Delete a contact
@app.delete("/contacts/{contact_id}", response_model=ContactResponse)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Deletes a contact by its ID.
    
    Args:
        contact_id (int): The ID of the contact to delete.
        db (Session): The database session.
        
    Returns:
        Contact: The deleted contact object.
        
    Raises:
        HTTPException: If the contact is not found.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(db_contact)
    db.commit()
    return db_contact


# Search contacts by first name, last name, or email
@app.get("/contacts/search/", response_model=List[ContactResponse])
def search_contacts(query: Optional[str] = Query(None), 
                    db: Session = Depends(get_db)):
    """
    Searches contacts by first name, last name, or email.
    
    Args:
        query (Optional[str]): The search query. Defeults to None.
        db (Session): The database session.
        
    Returns:
        List[Contact]: A list of matching contacts.
    """
    if query:
        contacts = db.query(Contact).filter(
            (Contact.first_name.ilike(f"%{query}%")) |
            (Contact.last_name.ilike(f"%{query}%")) |
            (Contact.email.ilike(f"%{query}%"))
        ).all()
        return contacts
    return []


# Get contacts with birthdays in the next 7 days
@app.get("/contacts/birthdays/", response_model=List[ContactResponse])
def upcoming_birthdays(db: Session = Depends(get_db)):
    """
    Retrieves contacts with birthdays in the next 7 days.
    
    Args:
        db (Session): The database session.
        
    Returns:
        List[Contact]: A list of contacts with upcoming bithdays.
    """
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    contacts = db.query(Contact).filter(
        (Contact.birthday >= today) & (Contact.birthday <= next_week)
    ).all()
    return contacts


@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), 
          db: Session = Depends(get_db)):
    """
    Authenticates a user and generates access and refresh tokens.
    
    Args:
        form_data (OAuth2PaswordRequestForm): The login form data.
        db (Session): The database session.
        
    Returns:
        Token: The generated access and refresh tokens.
        
    Raises:
        HTTPException: If the credentials are invalid.
    """
    user = db.query(User).filter(
        User.email == form_data.username
        ).first()
    if not user or not verify_password(form_data.password, 
                                       user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    return {"access_token": access_token, 
            "refresh_token": refresh_token, 
            "token_type": "bearer"}


@app.post("/contacts/", response_model=ContactResponse)
@limiter.limit("5/minute")
def create_contact(request: Request, contact: ContactCreate,
                   db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """
    Creates a new contact for the authenticated user.
    
    Args:
        contact (ContactCreate): The contact data to create.
        db (Session): The database session.
        current_user (User): The currently authenticated user.
        
    Returns:
        Contact: The created contact object.
        
    Raises:
        HTTPException: If a ontact with the same email already exists.
    """
    existing_contact = db.query(Contact).filter(
        Contact.email == contact.email,
        Contact.user_id == current_user.id
    ).first()

    if existing_contact:
        raise HTTPException(
            status_code=400,
            detail="Contact with this email already exists"
        )
    
    db_contact = Contact(**contact.model_dump(), user_id=current_user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@app.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user and sends a verification email.
    
    Args:
        user (UserCreate): The user data for registration.
        db (Session): The database session.
        
    Returns:
        UserResponse: The registered user object.
        
    Raises:
        HTTPException: If the email is already registered.
    """
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    hashed_password = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    verification_token = create_access_token({"sub": new_user.email})
    send_verification_email(new_user.email, verification_token)

    return new_user


@app.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verifies a user's email using a token.
    
    Args:
        token (str): The email verification token.
        db (Session): The database session.
        
    Returns:
        dict: A success message if the email is verified.
        
    Raises:
        HTTPExcepion: If the token is invalid, the user is not found, or the email is alreay verified.
    """
    try:
        payload = verify_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.is_verified:
            raise HTTPException(status_code=400, detail="Email already verified")
        
        user.is_verified = True
        db.commit()
        return {"message": "Email successfully verified"}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")
    