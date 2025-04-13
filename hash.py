from werkzeug.security import generate_password_hash

# Define the password you want to hash
plain_password = "san@123"

# Generate the hashed password
hashed_password = generate_password_hash(plain_password)

print("Hashed Password:", hashed_password)
