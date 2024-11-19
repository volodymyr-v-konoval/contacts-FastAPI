from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from auth import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user
from database import engine, get_db
from models import Base, Contact, User
from schemas import ContactCreate, Contact, UserCreate, UserResponse, Token

Base.metadata.create_all(bind=engine)


app = FastAPI()


# Get all contacts
@app.get("/contacts/", response_model=List[Contact])
def read_contacts(skip: int = 0, 
                  limit: int = 100, 
                  db: Session = Depends(get_db)):
    contacts = db.query(Contact).offset(skip).limit(limit).all()
    return contacts


# Get a single contact by ID
@app.get("/contacts/{contact_id}", response_model=Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact


# Update a contact
@app.put("/contacts/{contact_id}", response_model=Contact)
def update_contact(contact_id: int, 
                   contact: ContactCreate, 
                   db: Session = Depends(get_db)):
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
@app.delete("/contacts/{contact_id}", response_model=Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(db_contact)
    db.commit()
    return db_contact


# Search contacts by first name, last name, or email
@app.get("/contacts/search/", response_model=List[Contact])
def search_contacts(query: Optional[str] = Query(None), 
                    db: Session = Depends(get_db)):
    if query:
        contacts = db.query(Contact).filter(
            (Contact.first_name.ilike(f"%{query}%")) |
            (Contact.last_name.ilike(f"%{query}%")) |
            (Contact.email.ilike(f"%{query}%"))
        ).all()
        return contacts
    return []


# Get contacts with birthdays in the next 7 days
@app.get("/contacts/birthdays/", response_model=List[Contact])
def upcoming_birthdays(db: Session = Depends(get_db)):
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    contacts = db.query(Contact).filter(
        (Contact.birthday >= today) & (Contact.birthday <= next_week)
    ).all()
    return contacts


@app.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=409, 
                            detail="Email already registered")
    hashed_password = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), 
          db: Session = Depends(get_db)):
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


@app.post("/contacts/", response_model=Contact)
def create_contact(contact: ContactCreate,
                   db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    existing_contact = db.query(Contact).filter(
        Contact.email == contact.email,
        Contact.user_id == current_user.id
    ).first()

    if existing_contact:
        raise HTTPException(
            status_code=400,
            detail="Contact with this email alreade exists"
        )
    
    db_contact = Contact(**contact.model_dump(), user_id=current_user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact