from app import create_app, db
from app.models import FacebookPage, User
import os
import sys

# Create the instance directory if it doesn't exist
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

app = create_app()

def store_page_token():
    """Store a Facebook Page token in the database."""
    
    print("This script will store a Facebook Page token in the database.")
    
    # Get user input
    username = input("Enter the username for the Facebook page owner: ")
    page_id = input("Enter the Facebook Page ID: ")
    page_name = input("Enter the Facebook Page name: ")
    page_token = input("Enter the Page Access Token: ")
    
    with app.app_context():
        # Find the user
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"User '{username}' not found. Creating a basic user...")
            from werkzeug.security import generate_password_hash
            user = User(username=username, email=f"{username}@example.com")
            user.password_hash = generate_password_hash("temppassword")
            db.session.add(user)
            db.session.commit()
            print(f"Created user {username} with temporary password 'temppassword'")
        
        # Check if the page already exists
        existing_page = FacebookPage.query.filter_by(page_id=page_id).first()
        
        if existing_page:
            print(f"Updating existing page: {existing_page.page_name}")
            existing_page.page_name = page_name
            existing_page.access_token = page_token
            existing_page.user_id = user.id
            existing_page.is_active = True
        else:
            print(f"Creating new page: {page_name}")
            new_page = FacebookPage(
                page_id=page_id,
                page_name=page_name,
                access_token=page_token,
                user_id=user.id,
                is_active=True
            )
            db.session.add(new_page)
        
        db.session.commit()
        print(f"Successfully stored/updated token for page: {page_name}")
        print("You can now restart your application and start using the Facebook Helpdesk!")

if __name__ == "__main__":
    store_page_token()
