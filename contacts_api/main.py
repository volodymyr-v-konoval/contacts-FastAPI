from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database import engine, get_db
from models import Base, Contact
from schemas import ContactCreate, Contact

Base.metadata.create_all(bind=engine)


app = FastAPI()


# Create a new contact
@app.post("/contacts/", response_model=Contact)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    db_contact = Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


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
    db_contact = db.query(Contact).filte(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    for var, value in vars(contact).items():
        setattr(db_contact, var, value) if value else None
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact
    

# Delete a contact
@app.delete("/contacts/{cntact_id}", response_model=Contact)
def delete_cntact(contact_id: int, db: Session = Depends(get_db)):
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
