from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from sqlalchemy.sql import func

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with Facebook Page integration
    fb_pages = db.relationship('FacebookPage', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class FacebookPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.String(64), unique=True)
    page_name = db.Column(db.String(128))
    access_token = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with customer conversations
    conversations = db.relationship('Conversation', backref='page', lazy='dynamic')
    
    def __repr__(self):
        return f'<FacebookPage {self.page_name}>'

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fb_id = db.Column(db.String(64), unique=True)
    name = db.Column(db.String(128))
    profile_pic = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with conversations
    conversations = db.relationship('Conversation', backref='customer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fb_page_id = db.Column(db.Integer, db.ForeignKey('facebook_page.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    status = db.Column(db.String(20), default='open')  # open, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with messages
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', 
                              order_by='Message.timestamp.asc()')
    
    def __repr__(self):
        return f'<Conversation {self.id}>'
        
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'))
    sender_type = db.Column(db.String(20))  # customer, agent
    sender_id = db.Column(db.String(64))   # fb_id for customer, user_id for agent
    message_text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.id}>'
