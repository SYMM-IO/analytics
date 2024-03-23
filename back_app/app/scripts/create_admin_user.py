from getpass import getpass

from app import db_session
from app.models import AdminUser
from security.security_utils import hash_password


def create_admin_user(username, password):
    hashed_password = hash_password(password)
    try:
        with db_session() as session:
            session.add(AdminUser(username=username, password=hashed_password))
        print(f"Admin user '{username}' created successfully.")
    except Exception as ex:
        print(ex)
        print("An admin user with this username already exists.")


def main():
    print("Create a new admin user")
    username = input("Username: ")
    password = getpass("Password: ")
    create_admin_user(username, password)


if __name__ == "__main__":
    main()
