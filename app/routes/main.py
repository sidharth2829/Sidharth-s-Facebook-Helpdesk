from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import FacebookPage, Conversation, Message

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html', title='Facebook Helpdesk')

@main.route('/dashboard')
@login_required
def dashboard():
    # Get Facebook pages integrated by the user
    pages = FacebookPage.query.filter_by(user_id=current_user.id).all()
    
    # If no pages, redirect to integration page
    if not pages:
        return redirect(url_for('integration.manage'))
    
    # Get all conversations from user's FB pages
    conversations = []
    for page in pages:
        page_conversations = Conversation.query.filter_by(fb_page_id=page.id).order_by(Conversation.updated_at.desc()).all()
        conversations.extend(page_conversations)
    
    # Sort conversations by updated_at timestamp (newest first)
    conversations.sort(key=lambda x: x.updated_at, reverse=True)
    
    return render_template('dashboard/index.html', title='Dashboard', 
                          pages=pages, conversations=conversations,Message=Message)
