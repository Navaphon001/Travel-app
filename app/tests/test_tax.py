import pytest
from fastapi.testclient import TestClient # ใช้ TestClient แบบ Synchronous
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base # จำเป็นต้องนำเข้า Base ที่นี่ด้วย

# นำเข้า app หลักของคุณ
from app.main import app 

# นำเข้า Base และ get_db จากไฟล์ database ของคุณ
# สมมติว่าโค้ดที่คุณให้มาอยู่ใน app/database.py
from app.database import Base, get_db, engine as app_engine # นำเข้า Base, get_db และ engine หลักของแอป

# นำเข้าโมเดล Tax ของคุณ
# สมมติว่า Tax อยู่ใน app/models.py
from app.models import Tax 

# --- การตั้งค่าฐานข้อมูลทดสอบ ---
# ใช้ฐานข้อมูล SQLite แบบ in-memory เพื่อความรวดเร็วและแยกการทดสอบ
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

# สร้าง Engine สำหรับฐานข้อมูลทดสอบ
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

# สร้าง SessionLocal สำหรับฐานข้อมูลทดสอบ
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# --- Fixtures สำหรับการทดสอบ ---

@pytest.fixture(name="session")
def session_fixture():
    """
    Fixture ที่ให้ Database Session สำหรับการทดสอบแต่ละครั้ง
    และจัดการการสร้าง/ลบตาราง
    """
    # สร้างตารางทั้งหมดในฐานข้อมูลทดสอบ
    # ต้องแน่ใจว่าโมเดลทั้งหมดถูก import หรือรู้จักโดย Base.metadata
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine) 
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # ลบตารางทั้งหมดหลังจากแต่ละการทดสอบเสร็จสิ้น
        Base.metadata.drop_all(test_engine)

@pytest.fixture(name="client")
def client_fixture(session):
    """
    Fixture ที่ให้ TestClient สำหรับการทดสอบ
    และ override dependency get_db ให้ใช้ session ทดสอบ
    """
    # ฟังก์ชันสำหรับ override get_db ใน app.main
    def override_get_db():
        yield session

    # Override dependency ใน app.main
    app.dependency_overrides[get_db] = override_get_db
    
    # สร้าง TestClient
    with TestClient(app) as client:
        yield client
    
    # ล้าง override หลังจาก test เสร็จ
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
    # เนื่องจาก fixture "session" จะล้างฐานข้อมูลก่อนแต่ละ test
    # เราสามารถใช้ "TestProvince" ซ้ำได้
    response = client.post(
        "/tax/",
        json=tax_data
    )
    assert response.status_code == 201 # หรือ 201 ถ้า API คืน 201 Created
    data = response.json()
    assert data["province"] == tax_data["province"]
    assert data["reduce_tax_percent"] == tax_data["reduce_tax_percent"]
    assert data["is_secondary"] == tax_data["is_secondary"]
    assert "id" in data # ควรมีการคืนค่า id กลับมาด้วย

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
    assert len(response.json()) >= 2 # ตรวจสอบว่ามีข้อมูลอย่างน้อย 2 รายการที่เราเพิ่มไป

# --- ตัวอย่างการทดสอบเคสข้อมูลซ้ำ ---

def test_create_tax_duplicate_province(client: TestClient, tax_data: dict):
    # สร้างจังหวัดครั้งแรก (ควรสำเร็จและคืน 201)
    response_initial = client.post("/tax/", json=tax_data)
    assert response_initial.status_code == 201 # คาดหวัง 201 สำหรับการสร้างครั้งแรก

    # พยายามสร้างอีกครั้งด้วยชื่อจังหวัดเดิม
    response_duplicate = client.post("/tax/", json=tax_data)

    # ⭐ แก้ไขตรงนี้ ⭐
    # คาดหวัง 400 Bad Request (หรือ 409 Conflict ถ้าคุณเลือกใช้ใน Router)
    assert response_duplicate.status_code == 400 
    assert "Province already exists." in response_duplicate.json()["detail"]