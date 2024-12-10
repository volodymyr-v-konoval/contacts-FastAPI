"""
This module defines the SQLAlchemy ORM models for the application's datavase.

Classes:
    Contact: Represents a contact entity with details such as name, email, phone number, and birthday.
    User: Represents a user entity with attributes like email, hashed password, and verification status.
"""

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base


class Contact(Base):
    """
    Represents a contact entity in the database.
    
    Attributes:
        id (int): The unique identifier of the contact.
        first_name (str): The first name of the contact.
        last_name (str): The last name of the contact.
        email (str): The email address of the contact (unique).
        phone_number (str): The phone number of the contact.
        birthday (date): The birthday of the contact.
        additional_data (str): Additional notes or information about the contact (ptional).
        user_if (int): The ID of the user who owns this contact (foreign key).
        owner (User): A relationship to the User who owns this contact.
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    birthday = Column(Date)
    additional_data = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="contacts")

class User(Base):
    """
    Represents a user entity in the database.
    
    Attributes:
        id (int): The unique identifier of the user.
        email (str): The email address of the user (unique).
        hashed_password (str): The hashed password of the user.
        is_active (bool): Indicates whether the user's email is verified (default: False).
        avatar_url (str): The URL to the user's avatar (optional).
        contacts (List[Contact]): A list of contacts owned by the user.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String, nullable=True)

    contacts = relationship("Contact", back_populates="owner")
    