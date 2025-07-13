import pytest
from fastapi.testclient import TestClient # ใช้ TestClient แบบ Synchronous
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base 

# นำเข้า app หลักของคุณ
from app.main import app 

# นำเข้า Base และ get_db จากไฟล์ database ของคุณ
from app.database import Base, get_db, engine as app_engine 

# นำเข้าโมเดล Tax ของคุณ
from app.models import Tax 

# --- การตั้งค่าฐานข้อมูลทดสอบ ---
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# --- Fixtures สำหรับการทดสอบ ---

@pytest.fixture(name="session")
def session_fixture():
    """
    Fixture ที่ให้ Database Session สำหรับการทดสอบแต่ละครั้ง
    และจัดการการสร้าง/ลบตาราง (เพื่อให้ฐานข้อมูลสะอาดเสมอ)
    """
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine) 
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # ไม่จำเป็นต้อง drop_all อีกครั้งถ้าเรียกก่อนแล้ว

@pytest.fixture(name="client")
def client_fixture(session):
    """
    Fixture ที่ให้ TestClient สำหรับการทดสอบ
    และ override dependency get_db ให้ใช้ session ทดสอบ
    """
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear() 

@pytest.fixture
def tax_data():
    """Fixture สำหรับข้อมูลภาษีทดสอบ."""
    return {
        "province": "TestProvince",
        "reduce_tax_percent": 10.0,
        "is_secondary": 1,
        "description": "จังหวัดทดสอบ"
    }

# --- Tests ของคุณ ---

def test_create_tax(client: TestClient, tax_data: dict):
    """
    ทดสอบการสร้างข้อมูลภาษีใหม่
    """
    response = client.post(
        "/tax/",
        json=tax_data
    )
    # ⭐ แก้ไข: คาดหวัง 201 Created เมื่อสร้างสำเร็จ ⭐
    assert response.status_code == 201 
    data = response.json()
    assert data["province"] == tax_data["province"]
    assert data["reduce_tax_percent"] == tax_data["reduce_tax_percent"]
    assert data["is_secondary"] == tax_data["is_secondary"]
    assert "id" in data

def test_get_all_taxes(client: TestClient):
    """
    ทดสอบการดึงข้อมูลภาษีทั้งหมด
    """
    # สร้างข้อมูลทดสอบบางส่วนก่อน เพื่อให้แน่ใจว่ามีข้อมูลให้ดึง
    client.post("/tax/", json={
        "province": "TestProvince_GET1", "reduce_tax_percent": 5.0, "is_secondary": 0, "description": "Desc1"
    })
    client.post("/tax/", json={
        "province": "TestProvince_GET2", "reduce_tax_percent": 7.0, "is_secondary": 1, "description": "Desc2"
    })

    response = client.get("/tax/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2 

# --- Test Case สำหรับข้อมูลซ้ำ ---
def test_create_tax_duplicate_province(client: TestClient, tax_data: dict):
    """
    ทดสอบการพยายามสร้างข้อมูลภาษีด้วย province ที่ซ้ำกัน
    ควรได้รับข้อผิดพลาด 400 (หรือ 409) จาก API
    """
    # 1. สร้างจังหวัดครั้งแรก (ควรสำเร็จและคืน 201)
    response_initial = client.post("/tax/", json=tax_data)
    assert response_initial.status_code == 201 

    # 2. พยายามสร้างอีกครั้งด้วยชื่อจังหวัดเดิม
    response_duplicate = client.post("/tax/", json=tax_data)

    # ⭐ แก้ไข: คาดหวัง 400 Bad Request สำหรับข้อมูลซ้ำ ⭐
    assert response_duplicate.status_code == 400 
    assert "Province already exists." in response_duplicate.json()["detail"]

# --- Test Case ใหม่: ดึงข้อมูล Tax ด้วย Province ที่ไม่มีอยู่จริง (คาดหวัง 404) ---
def test_get_tax_by_non_existent_province(client: TestClient):
    """
    ทดสอบการดึงข้อมูลภาษีด้วย province ที่ไม่มีอยู่ในระบบ
    ควรคืนค่า 404 Not Found
    """
    non_existent_province = "NonExistentProvince"
    get_resp = client.get(f"/tax/{non_existent_province}") # แก้ไข path ให้ตรงกับ router ของคุณ

    # ⭐ คาดหวัง 404 Not Found ⭐
    assert get_resp.status_code == 404
    assert get_resp.json()["detail"] == "Tax info not found" # ข้อความ Error ที่คุณกำหนดใน Router