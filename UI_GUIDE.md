# Healthcare Authentication System - UI Guide

## Overview

A modern, clean web interface for the Privacy-Preserving Mutual Authentication System. This UI provides an intuitive way to interact with the healthcare authentication protocol without using command-line tools.

## Features

- **User Registration**: Register new users and receive smartcard credentials
- **User Authentication**: Authenticate with healthcare servers and establish secure sessions
- **System Status Monitoring**: Real-time status of all backend services
- **Clean Modern Design**: Responsive, gradient-based healthcare-themed interface
- **Interactive Elements**: Click-to-copy functionality for credentials and session keys
- **Error Handling**: Clear error messages and validation

## Quick Start

### Prerequisites

Make sure you have the following installed:
- Python 3.7+
- pip (Python package manager)

### Installation

Install the required dependencies:

```bash
pip install fastapi uvicorn flask requests python-multipart
```

### Running the Application

#### Option 1: Using the Startup Script (Recommended)

**On Linux/Mac:**
```bash
./start_ui.sh
```

**On Windows:**
```batch
start_ui.bat
```

This will automatically start all three services:
- Registration Center (port 5000)
- Healthcare Server (port 5001)
- Middleware + UI (port 8000)

#### Option 2: Manual Startup

Open **three separate terminals** and run:

**Terminal 1 - Registration Center:**
```bash
python rc.py
```

**Terminal 2 - Healthcare Server:**
```bash
python server1.py
```

**Terminal 3 - Middleware & UI:**
```bash
uvicorn middleware:app --host 0.0.0.0 --port 8000 --reload
```

### Accessing the UI

Once all services are running, open your browser and navigate to:

```
http://localhost:8000
```

## Using the UI

### 1. User Registration

1. Navigate to the **User Registration** section
2. Enter a unique User ID (alphanumeric only)
3. Enter a secure password
4. Click **Register**
5. Upon success, you'll receive your smartcard credentials:
   - `W_i`, `X_i`, `Y_i`, `Z_i`, `E_i`
6. Click on any credential value to copy it to clipboard

### 2. User Authentication

1. Navigate to the **User Authentication** section
2. Enter your registered User ID
3. Enter your password
4. Click **Authenticate**
5. Upon success, you'll receive:
   - Session Key (`SK_ij`)
   - Timestamp of authentication
   - Secure connection status indicator

### 3. System Status

The bottom section shows real-time status of all services:
- **Registration Center** - Green dot indicates online
- **Healthcare Server** - Green dot indicates online
- **Middleware API** - Green dot indicates online

Status updates automatically every 30 seconds.

## File Structure

```
project/
├── index.html              # Main UI page
├── static/
│   ├── styles.css         # UI styling
│   └── app.js             # JavaScript logic
├── middleware.py          # FastAPI middleware (updated)
├── rc.py                  # Registration Center
├── server1.py             # Healthcare Server
├── start_ui.sh            # Linux/Mac launcher
├── start_ui.bat           # Windows launcher
└── UI_GUIDE.md            # This file
```

## Configuration

The UI connects to the following endpoints by default:

```javascript
API_BASE_URL = 'http://localhost:8000'  // Middleware
RC_URL = 'http://localhost:5000'        // Registration Center
SERVER_URL = 'http://localhost:5001'    // Healthcare Server
```

To change ports, update:
1. The configuration in `static/app.js`
2. Environment variables or hardcoded values in Python files

## Features in Detail

### Click-to-Copy
All credential values and session keys are clickable. Click any value to copy it to your clipboard.

### Auto-Hide Errors
Error messages automatically hide after 5 seconds.

### Input Validation
- User IDs are automatically filtered to allow only alphanumeric characters and underscores
- Empty fields are validated before submission

### Loading States
Buttons show loading spinners during API calls to provide visual feedback.

### Responsive Design
The UI adapts to different screen sizes and works on mobile devices.

## Troubleshooting

### UI doesn't load
- Ensure `middleware.py` is running on port 8000
- Check browser console for errors (F12)
- Verify `index.html` is in the root directory

### Services show as "Offline"
- Ensure all three services are running
- Check firewall settings
- Verify ports 5000, 5001, and 8000 are not in use by other applications

### CORS Errors
- The middleware has CORS enabled for all origins
- If issues persist, check browser console and ensure you're accessing via `http://localhost:8000`

### Registration Fails
- Ensure the Registration Center is running
- Check if the User ID already exists
- Verify the Healthcare Server is registered with RC

### Authentication Fails
- Ensure you've registered first
- Check User ID and password are correct
- Verify all services are running and healthy
- Check that `user_data.json` exists and contains your smartcard

## Security Notes

**Important:** This UI is for development and testing purposes. For production use:

1. Change CORS settings in `middleware.py` to specify allowed origins
2. Use HTTPS/TLS for all communications
3. Implement proper session management
4. Add rate limiting and request validation
5. Encrypt the `user_data.json` file
6. Use secure password hashing and storage
7. Implement proper authentication tokens

## API Endpoints

The middleware exposes the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves the UI |
| `/health` | GET | Health check |
| `/register_user` | POST | User registration |
| `/authenticate_user` | POST | User authentication |

## Customization

### Changing Colors

Edit `static/styles.css` and modify the CSS variables:

```css
:root {
    --primary-color: #2563eb;      /* Main blue */
    --secondary-color: #10b981;    /* Success green */
    --danger-color: #ef4444;       /* Error red */
    /* ... more variables ... */
}
```

### Adding New Features

1. Update `index.html` to add UI elements
2. Add styling in `static/styles.css`
3. Implement logic in `static/app.js`
4. Add backend endpoints in `middleware.py` if needed

## Support

For issues related to:
- **UI/Frontend**: Check browser console and `static/app.js`
- **Backend**: Check terminal output and log files
- **Authentication Flow**: Refer to the original paper (IEEE Access 2020)

## Credits

Based on the paper:
**"Privacy-Preserving Mutual Authentication and Key Agreement Scheme for Multi-Server Healthcare System"**
_Limbasiya, Sahay, Sridharan – IEEE Access, 2020_
