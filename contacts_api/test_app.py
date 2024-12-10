from fastapi.testclient import TestClient
from main import app  
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db  
from models import User, Contact
from schemas import ContactCreate

# Налаштування для бази даних для тестування
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"  # Використовуємо in-memory базу даних для тестування
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Створення таблиць для тестів
Base.metadata.create_all(bind=engine)

# Мокання бази даних
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Створення тестових даних
def create_test_user():
    db = SessionLocal()
    user = User(email="testuser@example.com", hashed_password="testpassword")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_create_contact():
    user = create_test_user()

    # Логін користувача і отримання токена
    response = client.post("/login", data={"username": "testuser@example.com", "password": "testpassword"})
    assert response.status_code == 200
    tokens = response.json()
    access_token = tokens["access_token"]

    # Додавання контактів для користувача
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "1234567890",
        "birthday": "1990-01-01"
    }

    # Тестування створення контакту
    response = client.post(
        "/contacts/",
        json=contact_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    contact = response.json()

    # Перевірка, чи був контакт успішно створений
    assert contact["first_name"] == "John"
    assert contact["last_name"] == "Doe"
    assert contact["email"] == "john.doe@example.com"
    assert contact["phone_number"] == "1234567890"
