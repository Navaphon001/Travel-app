import pytest
import pytest_asyncio
from httpx import AsyncClient # ต้อง import AsyncClient จาก httpx
from sqlmodel import SQLModel, create_engine, Session # ใช้ Session จาก sqlmodel สำหรับการจัดการ sync session ใน fixture
from sqlmodel.ext.asyncio.session import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# ควรจะนำเข้า app จากไฟล์หลักของคุณ (อาจจะเป็น app.main)
from app.main import app 

# ตรวจสอบให้แน่ใจว่า import โมเดล Tax ของคุณถูกต้อง
# ถ้าโมเดล Tax อยู่ใน app.models, ก็จะเป็น from app.models import Tax
# ถ้า Tax อยู่ในไฟล์อื่น เช่น app.schemas หรือ app.crud, ปรับให้ถูกต้อง
from app.models import Tax 

# สำหรับการตั้งค่าฐานข้อมูลทดสอบ
# แนะนำให้ใช้ตัวแปรสภาพแวดล้อม หรือกำหนดค่าตรงนี้สำหรับ dev/test
DATABASE_URL = "sqlite+aiosqlite:///./test.db" # ฐานข้อมูลทดสอบ
# หรือจะใช้ in-memory database ก็ได้: DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# --- Fixtures สำหรับการตั้งค่าฐานข้อมูลทดสอบ ---

# สร้าง AsyncEngine สำหรับการเชื่อมต่อฐานข้อมูลทดสอบ
# ใช้ autouse=True เพื่อให้รันก่อนทุก test
@pytest_asyncio.fixture(name="engine", scope="session", autouse=True)
async def engine_fixture():
    engine = create_async_engine(DATABASE_URL, echo=False) # echo=True เพื่อดู SQL logs
    
    # สร้างตารางทั้งหมด (ล้างของเก่าถ้ามี)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all) # ลบตารางที่มีอยู่ทั้งหมด
        await conn.run_sync(SQLModel.metadata.create_all) # สร้างตารางใหม่ทั้งหมด
    yield engine
    # โค้ดส่วนนี้จะรันหลังจากทุก test เสร็จสิ้น (cleanup)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all) # ลบตารางอีกครั้งเพื่อความสะอาด
    await engine.dispose() # ปิดการเชื่อมต่อ engine

# Override get_session dependency สำหรับการทดสอบ
# ให้ใช้ session จากฐานข้อมูลทดสอบแทน
@pytest_asyncio.fixture(name="session")
async def session_fixture(engine):
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session

# Override dependency ใน app.main
@pytest_asyncio.fixture(name="client")
async def client_fixture(session):
    # ฟังก์ชันสำหรับ override get_session ใน app.main
    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override # ใช้ session ทดสอบ
    
    # สร้าง TestClient ด้วย httpx.AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear() # ล้าง override หลังจาก test เสร็จ

# --- Fixture สำหรับข้อมูลทดสอบ ---
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

@pytest.mark.asyncio
async def test_create_tax(client: AsyncClient, tax_data: dict):
    # ส่งข้อมูลแบบไม่ซ้ำกันในแต่ละครั้งเพื่อหลีกเลี่ยง UNIQUE constraint
    # หรือใช้ fixture cleanup_db_after_test เหมือนในตัวอย่าง test_customer_duplicate_email ของอาจารย์
    # แต่การสร้างชื่อไม่ซ้ำกันชั่วคราวเป็นวิธีที่ง่ายกว่าสำหรับ test_create_tax โดยตรง
    unique_province_name = f"{tax_data['province']}_{pytest.nodeid.split('::')[-1]}" 
    # ใช้ pytest.nodeid เพื่อให้ชื่อ unique ต่อ test function call

    test_data = tax_data.copy()
    test_data["province"] = unique_province_name

    response = await client.post(
        "/tax/",
        json=test_data
    )
    assert response.status_code == 201 # ควรเป็น 201 Created สำหรับการสร้างทรัพยากรใหม่
    data = response.json()
    assert data["province"] == unique_province_name
    assert data["reduce_tax_percent"] == 10.0
    assert data["is_secondary"] == 1
    assert "id" in data # ควรมีการคืนค่า id กลับมาด้วย

@pytest.mark.asyncio
async def test_get_all_taxes(client: AsyncClient):
    # สร้างข้อมูลทดสอบบางส่วนก่อน เพื่อให้แน่ใจว่ามีข้อมูลให้ดึง
    await client.post("/tax/", json={
        "province": "TestProvince_GET1", "reduce_tax_percent": 5.0, "is_secondary": 0, "description": "Desc1"
    })
    await client.post("/tax/", json={
        "province": "TestProvince_GET2", "reduce_tax_percent": 7.0, "is_secondary": 1, "description": "Desc2"
    })

    response = await client.get("/tax/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2 # ตรวจสอบว่ามีข้อมูลอย่างน้อย 2 รายการที่เราเพิ่มไป

# --- ตัวอย่างการปรับใช้จากโค้ดอาจารย์เพิ่มเติม ---

@pytest.mark.asyncio
async def test_create_tax_duplicate_province(client: AsyncClient, tax_data: dict):
    # สร้าง province ครั้งแรก
    response_initial = await client.post("/tax/", json=tax_data)
    assert response_initial.status_code == 201

    # พยายามสร้างอีกครั้งด้วย province เดิม
    response_duplicate = await client.post("/tax/", json=tax_data)
    
    # ควรคืนค่า 400 Bad Request หรือ 409 Conflict สำหรับข้อมูลซ้ำ
    # คุณต้องปรับใน API ของคุณให้ return status_code ที่เหมาะสมด้วย
    assert response_duplicate.status_code == 400 
    assert "Province already exists" in response_duplicate.json()["detail"] # ตรวจสอบข้อความ error