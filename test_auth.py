from app.auth import get_password_hash, verify_password

hashed = get_password_hash("mypassword")
print("Hashed:", hashed)

assert verify_password("mypassword", hashed) == True
assert verify_password("wrongpass", hashed) == False

print("Test auth success!")
