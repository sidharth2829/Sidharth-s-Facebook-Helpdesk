from app import create_app, db, socketio
from app.models import User, FacebookPage, Customer, Conversation, Message

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'FacebookPage': FacebookPage,
        'Customer': Customer,
        'Conversation': Conversation,
        'Message': Message
    }

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001, allow_unsafe_werkzeug=True)
