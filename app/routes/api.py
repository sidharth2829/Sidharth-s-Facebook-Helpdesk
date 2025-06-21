from flask import Blueprint, request, jsonify, current_app
from app import db, socketio
from app.models import FacebookPage, Customer, Conversation, Message
from datetime import datetime, timedelta
import requests
import json

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Handle webhook verification
        verify_token = current_app.config['FB_WEBHOOK_VERIFY_TOKEN']
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode and token:
            if mode == 'subscribe' and token == verify_token:
                print("WEBHOOK_VERIFIED")
                return challenge, 200
        
        return "Verification failed", 403
    
    elif request.method == 'POST':
        # Handle incoming webhook events
        try:
            data = request.json
            print(f"Webhook received: {json.dumps(data)}")
            
            # Ensure this is a page webhook event
            if data.get('object') == 'page':
                for entry in data.get('entry', []):
                    page_id = entry.get('id')
                    messaging_events = entry.get('messaging', [])
                    
                    # Process each messaging event
                    for event in messaging_events:
                        process_messaging_event(event, page_id)
            
            return "EVENT_RECEIVED", 200
        except Exception as e:
            print(f"Webhook error: {str(e)}")
            return "Error processing webhook", 500

def process_messaging_event(event, fb_page_id):
    """Process a Facebook Messenger event and store in database"""
    sender_id = event.get('sender', {}).get('id')
    recipient_id = event.get('recipient', {}).get('id')
    timestamp = event.get('timestamp')
    message_data = event.get('message', {})
    
    # Ignore messages sent by the page itself
    if sender_id == recipient_id:
        return
    
    try:
        # Get the page from our database
        page = FacebookPage.query.filter_by(page_id=fb_page_id).first()
        if not page:
            print(f"Page not found in database: {fb_page_id}")
            return
        
        # Get or create customer
        customer = Customer.query.filter_by(fb_id=sender_id).first()
        if not customer:
            # Fetch customer info from Facebook
            user_url = f"https://graph.facebook.com/{sender_id}"
            params = {
                'fields': 'name,profile_pic',
                'access_token': page.access_token
            }
            response = requests.get(user_url, params=params)
            user_data = response.json()
            
            customer = Customer(
                fb_id=sender_id,
                name=user_data.get('name', 'Unknown User'),
                profile_pic=user_data.get('profile_pic', '')
            )
            db.session.add(customer)
            db.session.commit()
        
        # Find existing conversation or create new one
        conversation = find_or_create_conversation(customer.id, page.id)
        
        # Store the message
        if message_data and message_data.get('text'):
            message = Message(
                conversation_id=conversation.id,
                sender_type='customer',
                sender_id=sender_id,
                message_text=message_data.get('text'),
                timestamp=datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.utcnow()
            )
            db.session.add(message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Emit Socket.IO event with the new message
            message_data = {
                'id': message.id,
                'conversation_id': conversation.id,
                'sender_type': message.sender_type,
                'sender_id': message.sender_id,
                'message_text': message.message_text,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'customer': {
                    'id': customer.id,
                    'name': customer.name,
                    'profile_pic': customer.profile_pic
                }
            }
            socketio.emit('new_message', message_data, room=f"conversation_{conversation.id}")
            # Also emit to the general room for conversation list updates
            socketio.emit('conversation_update', {
                'conversation_id': conversation.id,
                'last_message': message.message_text[:30] + ('...' if len(message.message_text) > 30 else ''),
                'updated_at': conversation.updated_at.strftime('%b %d, %H:%M')
            })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error processing message: {str(e)}")

def find_or_create_conversation(customer_id, fb_page_id):
    """Find existing conversation or create a new one"""
    # Check for existing conversation in last 24 hours
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    
    conversation = Conversation.query.filter_by(
        customer_id=customer_id, 
        fb_page_id=fb_page_id
    ).filter(
        Conversation.updated_at >= cutoff_time
    ).order_by(
        Conversation.updated_at.desc()
    ).first()
    
    if conversation:
        return conversation
    
    # Create new conversation
    conversation = Conversation(
        fb_page_id=fb_page_id,
        customer_id=customer_id,
        status='open'
    )
    db.session.add(conversation)
    db.session.commit()
    
    return conversation

@api.route('/send-message', methods=['POST'])
def send_message():
    """Send a message to a Facebook user"""
    data = request.json
    conversation_id = data.get('conversation_id')
    message_text = data.get('message')
    user_id = data.get('user_id')
    
    if not all([conversation_id, message_text, user_id]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Get conversation and related data
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        page = FacebookPage.query.get(conversation.fb_page_id)
        customer = Customer.query.get(conversation.customer_id)
        
        if not page or not customer:
            return jsonify({'error': 'Page or customer not found'}), 404
        
        # Send message to Facebook
        url = f"https://graph.facebook.com/v18.0/me/messages"
        payload = {
            'recipient': {'id': customer.fb_id},
            'message': {'text': message_text},
            'messaging_type': 'RESPONSE'
        }
        params = {'access_token': page.access_token}
        
        response = requests.post(url, json=payload, params=params)
        response_data = response.json()
        
        if response.status_code != 200 or response_data.get('error'):
            return jsonify({'error': 'Failed to send message to Facebook', 'details': response_data}), 400
        
        # Store message in our database
        message = Message(
            conversation_id=conversation.id,
            sender_type='agent',
            sender_id=user_id,
            message_text=message_text
        )
        db.session.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Emit Socket.IO event with the new message
        message_time = message.timestamp.strftime('%H:%M')
        socketio.emit('new_message', {
            'id': message.id,
            'conversation_id': conversation.id,
            'sender_type': 'agent',
            'sender_id': user_id,
            'message_text': message_text,
            'timestamp': message_time
        }, room=f"conversation_{conversation.id}")
        
        # Also emit to the general room for conversation list updates
        socketio.emit('conversation_update', {
            'conversation_id': conversation.id,
            'last_message': message_text[:30] + ('...' if len(message_text) > 30 else ''),
            'updated_at': conversation.updated_at.strftime('%b %d, %H:%M')
        })
        
        return jsonify({
            'success': True, 
            'message': 'Message sent successfully',
            'message_time': message_time
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api.route('/conversation/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get conversation data including messages"""
    try:
        # Get conversation and check if it exists
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Get all messages for the conversation
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
        
        # Get customer data
        customer = Customer.query.get(conversation.customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Format message data
        message_data = []
        for message in messages:
            message_data.append({
                'id': message.id,
                'sender_type': message.sender_type,
                'sender_id': message.sender_id,
                'message_text': message.message_text,
                'timestamp': message.timestamp.strftime('%H:%M')
            })
        
        # Format customer data
        customer_data = {
            'id': customer.id,
            'fb_id': customer.fb_id,
            'name': customer.name,
            'profile_pic': customer.profile_pic,
            'created_at': customer.created_at.strftime('%B %d, %Y')
        }
        
        # Format conversation data
        conversation_data = {
            'id': conversation.id,
            'status': conversation.status,
            'created_at': conversation.created_at.strftime('%B %d, %Y %H:%M'),
            'updated_at': conversation.updated_at.strftime('%B %d, %Y %H:%M')
        }
        
        return jsonify({
            'success': True,
            'conversation': conversation_data,
            'customer': customer_data,
            'messages': message_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
