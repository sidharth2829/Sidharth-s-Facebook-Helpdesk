from flask import Blueprint, render_template, redirect, url_for, current_app, request, flash, session, jsonify
from flask_login import login_required, current_user
import requests
from app import db
from app.models import FacebookPage
import json
import os

integration = Blueprint('integration', __name__, url_prefix='/integration')

@integration.route('/manage')
@login_required
def manage():
    # Get user's integrated Facebook pages
    pages = FacebookPage.query.filter_by(user_id=current_user.id).all()
    return render_template('integration/manage.html', title='Manage Facebook Integration', pages=pages)

@integration.route('/connect')
@login_required
def connect():
    # Generate Facebook Login URL with required permissions
    fb_app_id = current_app.config['FB_APP_ID']
    redirect_uri = current_app.config['FB_REDIRECT_URI']
    
    fb_login_url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={fb_app_id}&redirect_uri={redirect_uri}&scope=pages_messaging,pages_show_list,pages_read_engagement,pages_manage_metadata"
    
    return redirect(fb_login_url)

@integration.route('/callback')
@login_required
def callback():
    error = request.args.get('error')
    if error:
        flash(f"Facebook authentication error: {error}")
        return redirect(url_for('integration.manage'))
    
    code = request.args.get('code')
    if not code:
        flash("Failed to get authorization code from Facebook")
        return redirect(url_for('integration.manage'))
    
    # Exchange code for access token
    fb_app_id = current_app.config['FB_APP_ID']
    fb_app_secret = current_app.config['FB_APP_SECRET']
    redirect_uri = current_app.config['FB_REDIRECT_URI']
    
    token_url = f"https://graph.facebook.com/v18.0/oauth/access_token?client_id={fb_app_id}&redirect_uri={redirect_uri}&client_secret={fb_app_secret}&code={code}"
    
    try:
        response = requests.get(token_url)
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            flash("Failed to obtain access token from Facebook")
            return redirect(url_for('integration.manage'))
        
        # Get long-lived access token
        long_lived_token_url = f"https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id={fb_app_id}&client_secret={fb_app_secret}&fb_exchange_token={access_token}"
        response = requests.get(long_lived_token_url)
        long_lived_token_data = response.json()
        long_lived_access_token = long_lived_token_data.get('access_token')
        
        if not long_lived_access_token:
            flash("Failed to obtain long-lived access token")
            return redirect(url_for('integration.manage'))
        
        # Get user's Facebook pages
        pages_url = "https://graph.facebook.com/v18.0/me/accounts"
        response = requests.get(pages_url, params={'access_token': long_lived_access_token})
        pages_data = response.json().get('data', [])
        
        if not pages_data:
            flash("No Facebook pages found or insufficient permissions")
            return redirect(url_for('integration.manage'))
        
        # Save pages to database
        for page in pages_data:
            page_id = page.get('id')
            page_name = page.get('name')
            page_access_token = page.get('access_token')
            
            # Check if page already exists
            existing_page = FacebookPage.query.filter_by(page_id=page_id).first()
            
            if existing_page:
                # Update existing page
                existing_page.page_name = page_name
                existing_page.access_token = page_access_token
                existing_page.is_active = True
                existing_page.user_id = current_user.id
            else:
                # Create new page
                new_page = FacebookPage(page_id=page_id, page_name=page_name, 
                                       access_token=page_access_token, user_id=current_user.id)
                db.session.add(new_page)
            
            # Subscribe to page webhooks
            subscribe_url = f"https://graph.facebook.com/v18.0/{page_id}/subscribed_apps"
            subscribe_data = {
                'access_token': page_access_token,
                'subscribed_fields': 'messages,messaging_postbacks,messaging_optins'
            }
            requests.post(subscribe_url, data=subscribe_data)
        
        db.session.commit()
        flash("Facebook pages connected successfully!")
        return redirect(url_for('integration.manage'))
    
    except Exception as e:
        flash(f"Error connecting Facebook pages: {str(e)}")
        return redirect(url_for('integration.manage'))

@integration.route('/disconnect/<int:page_id>', methods=['POST'])
@login_required
def disconnect(page_id):
    page = FacebookPage.query.get_or_404(page_id)
    
    # Check if page belongs to current user
    if page.user_id != current_user.id:
        flash("You don't have permission to disconnect this page")
        return redirect(url_for('integration.manage'))
    
    try:
        # Unsubscribe from webhooks
        unsubscribe_url = f"https://graph.facebook.com/v18.0/{page.page_id}/subscribed_apps"
        requests.delete(unsubscribe_url, params={'access_token': page.access_token})
        
        # Mark page as inactive or delete
        db.session.delete(page)
        db.session.commit()
        
        flash("Facebook page disconnected successfully")
    except Exception as e:
        flash(f"Error disconnecting page: {str(e)}")
    
    return redirect(url_for('integration.manage'))
