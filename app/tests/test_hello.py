from app.auth import create_access_token
def test_create_access_token():
    data = {"sub": "test_user"}
    token = create_access_token(data)
    assert token is not None
    assert isinstance(token, str)