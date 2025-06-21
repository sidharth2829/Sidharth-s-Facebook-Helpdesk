from flask import request
from flask_socketio import join_room, leave_room, emit
from app import socketio

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('join')
def handle_join(data):
    """Handle joining a specific conversation room"""
    conversation_id = data.get('conversation_id')
    if conversation_id:
        room = f"conversation_{conversation_id}"
        join_room(room)
        print(f"Client {request.sid} joined room: {room}")
        emit('join_response', {'status': 'success', 'room': room}, room=request.sid)

@socketio.on('leave')
def handle_leave(data):
    """Handle leaving a specific conversation room"""
    conversation_id = data.get('conversation_id')
    if conversation_id:
        room = f"conversation_{conversation_id}"
        leave_room(room)
        print(f"Client {request.sid} left room: {room}")
