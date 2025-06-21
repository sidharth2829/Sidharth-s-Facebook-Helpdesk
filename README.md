# Facebook Helpdesk

## Overview
Facebook Helpdesk is a web application built with Flask that allows businesses to manage their Facebook Messenger conversations in a central dashboard. It enables customer support agents to respond to customer messages efficiently, keeping track of conversation history, and providing a better customer service experience.

## Features
- User registration and authentication
- Facebook Page integration with OAuth
- Real-time message synchronization via webhooks
- Threaded conversations with customers
- Agent response interface
- Customer profile information
- Conversation management (view, reply, mark as resolved)
- Real-time updates with websockets (Socket.IO)

## Tech Stack
- **Backend**: Flask (Python web framework)
- **Database**: SQLAlchemy with SQLite (configurable for other databases)
- **Authentication**: Flask-Login, Werkzeug security
- **Frontend**: Bootstrap 5, JavaScript, Socket.IO
- **External API**: Facebook Graph API

## Project Structure
```
fb-helpdesk/
├── app/ - Main application package
│   ├── __init__.py - Application factory
│   ├── models.py - Database models
│   ├── forms.py - WTForms definitions
│   ├── socket.py - Socket.IO event handlers
│   ├── routes/ - Blueprint routes
│   │   ├── api.py - API endpoints including webhooks
│   │   ├── auth.py - Authentication routes
│   │   ├── integration.py - Facebook integration
│   │   └── main.py - Main application routes
│   ├── static/ - Static assets
│   └── templates/ - Jinja2 templates
├── instance/ - Instance-specific data (database)
├── migrations/ - Database migrations
├── config.py - Application configuration
├── setup_db.py - Database initialization script
├── run.py - Development server script
├── requirements.txt - Application dependencies
```

## Installation

### Prerequisites
- Python 3.8+
- pip
- Facebook Developer Account and App
- ngrok (for local webhook testing)

### Local Development Setup

1. Clone the repository:
```
git clone https://github.com/yourusername/fb-helpdesk.git
cd fb-helpdesk
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```
SECRET_KEY=your_secret_key
FB_APP_ID=your_facebook_app_id
FB_APP_SECRET=your_facebook_app_secret
FB_REDIRECT_URI=https://your-domain.com/integration/callback
FB_WEBHOOK_VERIFY_TOKEN=your_webhook_verification_token
FB_PAGE_TOKEN=your_facebook_page_token
```

5. Initialize the database:
```
python setup_db.py
```

6. Run the development server:
```
python run.py
```

7. Start ngrok for webhook tunneling (in a separate terminal):
```
ngrok http 5001
```

8. Update your Facebook App Webhook URL with your ngrok URL:
   - Copy the HTTPS URL from ngrok (looks like `https://a1b2c3d4.ngrok.io`)
   - Set your webhook URL in Facebook Developer portal to `https://your-ngrok-url/api/webhook`
   - Update your `.env` file with:
     ```
     FB_REDIRECT_URI=https://your-ngrok-url/integration/callback
     ```

9. Access the application at http://127.0.0.1:5001

### Setting Up Facebook App Integration

1. Create a Facebook Developer Account and App at https://developers.facebook.com/
2. Configure the Facebook App:
   - Add the Messenger product
   - Under Messenger Settings, generate a Page Access Token
   - Set up Webhooks with your ngrok URL + `/api/webhook`
   - Subscribe to webhook events: messages, messaging_postbacks
3. Add the Page Access Token to your `.env` file as `FB_PAGE_TOKEN`

## Deployment

### Environment Configuration
For any deployment platform, ensure these environment variables are set:
- `SECRET_KEY`
- `FB_APP_ID`
- `FB_APP_SECRET`
- `FB_REDIRECT_URI`
- `FB_WEBHOOK_VERIFY_TOKEN`
- `FB_PAGE_TOKEN`
- `DATABASE_URL` (optional, for production database)


## Usage

### Default Admin Account
After running `setup_db.py`, an admin account is created:
- Username: `admin`
- Password: `adminpass`

### Integration Steps
1. Log in to the application
2. Go to the Integration page
3. Click "Connect Facebook Page"
4. Authorize your Facebook Page
5. Start receiving and responding to messages

## Development

### Adding New Features
1. Create a new branch for your feature
2. Add routes in the appropriate blueprint file
3. Update models if needed
4. Create templates for new views
5. Run tests and verify functionality
6. Submit a pull request


## Troubleshooting

### Facebook Integration Issues
- Ensure your app is properly configured on the Facebook Developer Dashboard
- Verify the webhook is accessible from the internet (use ngrok for local testing)
- Check that the Page Access Token has the correct permissions

### Ngrok Issues
- If your webhooks aren't receiving events, check your ngrok tunnel status
- Ngrok URLs expire after a few hours on the free plan. When you restart ngrok:
  1. Copy the new ngrok URL
  2. Update your Facebook Webhook URL in the Developer Portal
  3. Update your `FB_REDIRECT_URI` in the `.env` file
  4. Restart your Flask application

- For local testing, make sure all testers are added to your Facebook App while in Development Mode
- Run `ngrok http 5001` to match the default port of the application

