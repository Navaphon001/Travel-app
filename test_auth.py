#from fastapi.testclient import TestClient
#from app.main import app

#def test_register():
#   client = TestClient(app)
#    response = client.post(
#        "/register/",
#        json={
#            "username": "testuser",
#            "password": "testpass",
#            "fullname": "ทดสอบ ผู้ใช้",
#            "phone": "0812345678"
#        }
#    )
#    assert response.status_code == 200