#!/usr/bin/env python3
import os
import sys
from app import create_app, db
from app.models import User, FacebookPage, Customer, Conversation, Message

def init_db():
    """Initialize the database with better error handling."""
    
    print("Starting database initialization...")
    
    # Create app instance
    app = create_app()
    
    # Check if instance directory exists, create if not
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_dir):
        print(f"Creating instance directory: {instance_dir}")
        os.makedirs(instance_dir)
    
    # Ensure instance dir is writable
    if not os.access(instance_dir, os.W_OK):
        print(f"Making instance directory writable: {instance_dir}")
        os.chmod(instance_dir, 0o777)
    
    # Database path
    db_path = os.path.join(instance_dir, 'app.db')
    print(f"Database path: {db_path}")
    
    # Touch database file if it doesn't exist
    if not os.path.exists(db_path):
        print("Creating empty database file")
        open(db_path, 'a').close()
        os.chmod(db_path, 0o666)
    
    # Ensure database file is writable
    if not os.access(db_path, os.W_OK):
        print("Making database file writable")
        os.chmod(db_path, 0o666)
    
    # Initialize database
    with app.app_context():
        try:
            print("Dropping all existing database tables...")
            db.drop_all()
            
            print("Creating all database tables...")
            db.create_all()
            print("Database tables created successfully!")
            
            # Create admin user
            print("Creating admin user...")
            admin = User(
                username='admin',
                email='admin@example.com'
            )
            admin.set_password('adminpass')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created with username 'admin' and password 'adminpass'")
            
            # Create Facebook page with token from environment
            page_token = os.environ.get('FB_PAGE_TOKEN')
            if page_token:
                print("Creating Facebook page with token from environment...")
                page = FacebookPage(
                    page_id='659870513883516',
                    page_name='Fd-HELPDESK',
                    access_token=page_token,
                    user_id=admin.id,
                    is_active=True
                )
                db.session.add(page)
                db.session.commit()
                print("Facebook page created successfully!")
                
            print("Database initialization complete!")
            return True
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            print("Database error details:", sys.exc_info())
            return False

if __name__ == "__main__":
    success = init_db()
    if success:
        print("Database setup completed successfully!")
    else:
        print("Database setup failed. See error messages above.")
        sys.exit(1)
