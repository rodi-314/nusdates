import hashlib


# Cybersecurity
SALT = '^+@r4FGb{?Xi'

password = 'password123'

database_password = f'{password}{SALT}'
hashed_password = hashlib.sha512(database_password.encode())

print(hashed_password.hexdigest())

print(tuple({'a': 1}.items())[0])
