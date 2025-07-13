def test_register(client):
    data = {
        "fullname": "นายสมชาย ใจดี",
        "phone": "0891234567",
        "username": "somchai",
        "password": "secure123"
    }
    response = client.post("/register", json=data)
    assert response.status_code == 200
    assert response.json()["username"] == "somchai"
