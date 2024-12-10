"""
This module defines Pydantic used for data validation and serialization in the application.

Classes:
    ContactBase: Base model for contact-related data with common fields.
    ContactCreate: Model for creating a new contact, inheriting from ContactBase.
    Contact: Model for a contact entity, including its database ID and enabling ORM mode.
    UserBase: Base model for user-related data with basic fields. 
    UserCreate: Model for creating a new user, inheriting for UserBase.
    UserResponse: Model for returning user details, uncluding user ID and avatar URL, with ORM mode enabled.
    Token: Model for representing authentication token with access and refresh tokens.
"""

from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

class ContactBase(BaseModel):
    """
    Base model for contact-related data.
    
    Attributes:
        first_name (str): The first name of the contact.
        last_name (str): The last name of the contact.
        email (EmailStr): The email address of the contact.
        phone_number (str): The phone number of the contact.
        birthday (date): The birthday of the contact.
        additional_data (str, optional): Additional notes or information about the contact.
    """
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_data: str = None


class ContactCreate(ContactBase):
    """
    Model for creating a new contact.
    
    Inherits:
        ContactBase: All fields required for a contact entity.
    """
    pass


class Contact(ContactBase):
    """
    Model representing a contact entity.
    
    Attributes:
        id (int): The unique identifier of the contact.
        
    Config:
        orm_mode (bool): Enables ORMmode to allow compatibility with SQLAlchemy models.
    """
    id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    """
    Base model for user-related data.
    
    Attributes:
        email (EmailStr): The email address of the user.
    """
    email: EmailStr


class UserCreate(UserBase):
    """
    Model for creating a new user.
    
    Inherits:
        UserBase: Includes the user's email.
        
    Attributes:
        password (str): The pasword for the new user.
    """
    password: str


class UserResponse(UserBase):
    """
    Model for returning user details.
    
    Attributes:
        id (int): The unique identifier of the user.
        avatar_url (str, optional): The URL to the user's avatar.
        
    Config:
        orm_mode (bool): Enables ORM mode to allow compatibility with SQLAlchemy models.
    """
    id: int
    avatar_url: Optional[str] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    """
    Model for representing authenrication tokens.
    
    Attributes:
        access_token (str): The access token used for authentication.
        refresh_token (str): The refresh token used for generating new access tokens.
        token_type (str): The type of token, default is "bearer".
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
