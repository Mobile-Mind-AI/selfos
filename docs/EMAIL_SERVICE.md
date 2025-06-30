# SelfOS Email Service Documentation

## Overview

The SelfOS Email Service provides comprehensive email functionality for user notifications, password resets, and system communications. The service is designed with a production-first approach, always attempting real SMTP email delivery when configured, with intelligent fallback to development mode when SMTP credentials are unavailable.

## Architecture

### Design Philosophy
- **Production-First**: Always attempts real email sending when SMTP credentials are available
- **Unified Mode**: No separate development/production modes - single email logic for all environments
- **Professional Templates**: High-quality HTML and text email templates with SelfOS branding
- **Security-Focused**: Built-in security warnings and best practices

### Key Components

```
EmailService (Singleton)
├── SMTP Email Sending (Primary)
├── Development Console Output (Fallback)
├── HTML Template Engine
├── Plain Text Template Engine
└── Configuration Management
```

## Configuration

### Environment Variables

The email service is configured via environment variables in `.env`:

```bash
# SMTP Configuration (Required for real email sending)
SMTP_SERVER=smtp.gmail.com          # SMTP server hostname
SMTP_PORT=587                       # SMTP port (587 for TLS)
SMTP_USERNAME=your-email@gmail.com  # SMTP authentication username
SMTP_PASSWORD=your-app-password     # SMTP authentication password

# Email Branding (Optional)
FROM_EMAIL=noreply@selfos.app       # Sender email address
FROM_NAME=SelfOS                    # Sender display name
```

### Gmail SMTP Setup

For Gmail SMTP (recommended for development and testing):

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Visit: https://myaccount.google.com/apppasswords
   - Select "Mail" as the app
   - Copy the generated 16-character password
3. **Configure Environment**:
   ```bash
   SMTP_USERNAME=youremail@gmail.com
   SMTP_PASSWORD="abcd efgh ijkl mnop"  # Quote if contains spaces
   FROM_EMAIL=noreply@yourcompany.com
   FROM_NAME=YourApp
   ```

### Docker Configuration

Email configuration is automatically loaded in Docker via `docker-compose.yml`:

```yaml
environment:
  SMTP_SERVER: smtp.gmail.com
  SMTP_PORT: 587
  SMTP_USERNAME: ${SMTP_USERNAME:-}
  SMTP_PASSWORD: ${SMTP_PASSWORD:-}
  FROM_EMAIL: ${FROM_EMAIL:-noreply@selfos.app}
  FROM_NAME: ${FROM_NAME:-SelfOS}
```

## Service Behavior

### Email Sending Logic

```python
if smtp_username and smtp_password:
    # Attempt real SMTP email sending
    return send_smtp_email(...)
else:
    # Show development console output with setup instructions
    return send_development_email(...)
```

### Real Email Mode
When SMTP credentials are configured:
- ✅ Sends actual emails via SMTP
- ✅ Professional HTML templates
- ✅ Plain text fallback
- ✅ Proper error handling
- ✅ Email delivery confirmation

### Development Mode
When SMTP credentials are missing:
- 📧 Displays email content in console
- 🔧 Shows clear setup instructions
- ⚠️ Provides configuration guidance
- 📋 Includes complete email content for testing

## Supported Email Types

### Password Reset Emails

**Features:**
- Professional HTML template with SelfOS branding
- Security warnings and best practices
- One-hour expiration notice
- Firebase authentication integration
- Plain text fallback version

**Template Components:**
- Header with SelfOS branding
- Personalized greeting
- Clear call-to-action button
- Security information panel
- Contact support information
- Professional footer

**Example Usage:**
```python
from services.email_service import email_service

success = email_service.send_password_reset_email(
    to_email="user@example.com",
    reset_link="https://app.com/reset/token123",
    user_name="John Doe"
)
```

## Integration Points

### Authentication Router
- **File**: `apps/backend_api/routers/auth.py`
- **Endpoint**: `POST /auth/forgot-password`
- **Integration**: Direct import and usage

```python
from services.email_service import email_service

# In forgot password endpoint
email_sent = email_service.send_password_reset_email(
    to_email=email,
    reset_link=link,
    user_name=user_name
)
```

### Firebase Authentication
- Generates secure password reset links
- Configures action code settings
- Handles link expiration (1 hour)
- Provides fallback for email delivery failures

## Email Templates

### HTML Template Features
- **Responsive Design**: Works across email clients
- **Professional Styling**: Consistent with SelfOS branding
- **Security Warnings**: Built-in security best practices
- **Call-to-Action**: Clear, prominent reset button
- **Accessibility**: Proper alt text and semantic HTML

### Template Structure
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
    <style>/* Professional CSS styling */</style>
</head>
<body>
    <div class="container">
        <div class="header">🔐 Password Reset Request</div>
        <div class="content">
            <!-- Personalized content -->
            <!-- Reset button -->
            <!-- Security warnings -->
        </div>
        <div class="footer">© 2025 SelfOS</div>
    </div>
</body>
</html>
```

### Plain Text Template
- Clean, readable format
- All essential information included
- Security warnings preserved
- Contact information provided

## Testing

### Unit Tests
- **File**: `tests/unit/test_auth.py`
- **Coverage**: Email service functionality via auth tests
- **Mocking**: Proper email service mocking for isolation

```python
@patch('services.email_service.email_service.send_password_reset_email')
def test_forgot_password_success(mock_send_email):
    mock_send_email.return_value = True
    # Test logic
```

### Manual Testing

#### Test Real Email Sending
```bash
# Configure SMTP credentials in .env
SMTP_USERNAME=test@gmail.com
SMTP_PASSWORD="your-app-password"

# Restart containers
docker-compose down && docker-compose up -d

# Test endpoint
curl -X POST "http://localhost:8000/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

#### Test Development Mode
```bash
# Remove SMTP credentials from .env
# SMTP_USERNAME=
# SMTP_PASSWORD=

# Restart containers
docker-compose down && docker-compose up -d

# Test endpoint - should show console output
curl -X POST "http://localhost:8000/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Check logs
docker-compose logs backend | tail -20
```

## Troubleshooting

### Common Issues

#### 1. SMTP Authentication Failed
**Error**: `Username and Password not accepted`

**Solutions**:
- Verify 2-factor authentication is enabled
- Use App Password, not regular Gmail password
- Check username format (full email address)
- Ensure password is quoted if it contains spaces

#### 2. Email Not Received
**Check**:
- SMTP credentials are correctly configured
- Email service logs show successful sending
- Recipient's spam/junk folder
- Email provider delivery delays

#### 3. Development Mode Not Working
**Verify**:
- SMTP credentials are not set in environment
- Container has latest code changes
- Check console logs for email content

### Debugging Commands

```bash
# Check environment variables
docker-compose exec backend printenv | grep SMTP

# View email service logs
docker-compose logs backend | grep EMAIL

# Test email endpoint
curl -X POST "http://localhost:8000/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## Security Considerations

### Email Security
- **SMTP over TLS**: All email traffic encrypted
- **App Passwords**: Use dedicated app passwords for Gmail
- **Link Expiration**: Password reset links expire in 1 hour
- **Security Warnings**: Built-in user education

### Data Protection
- **No Sensitive Data**: Email templates don't include passwords
- **Minimal Logging**: Email addresses logged for debugging only
- **Secure Storage**: SMTP credentials in environment variables

## Performance

### Current Performance
- **Synchronous Sending**: Emails sent inline with requests
- **Fast Fallback**: Development mode is instant
- **Error Handling**: Graceful degradation on failures

### Future Improvements
- **Async Sending**: Queue emails for background processing
- **Delivery Tracking**: Email delivery confirmation
- **Template Caching**: Cache compiled templates
- **Rate Limiting**: Prevent email spam

## Extension Points

### Adding New Email Types

1. **Add Template Methods**:
   ```python
   def _generate_welcome_email_html(self, user_name, login_link):
       # HTML template
   
   def _generate_welcome_email_text(self, user_name, login_link):
       # Plain text template
   ```

2. **Add Service Method**:
   ```python
   def send_welcome_email(self, to_email, user_name, login_link):
       # Implementation
   ```

3. **Integrate with Router**:
   ```python
   from services.email_service import email_service
   
   email_service.send_welcome_email(...)
   ```

### Template Customization

Templates can be customized by modifying the generation methods in `EmailService`:
- `_generate_password_reset_html()`
- `_generate_password_reset_text()`

### External Email Services

Future integration with services like SendGrid or AWS SES:
1. Create new email provider classes
2. Add provider selection logic
3. Maintain consistent interface

## Configuration Examples

### Production Configuration
```bash
# Production SMTP (e.g., SendGrid)
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@yourcompany.com
FROM_NAME=YourApp
```

### Development Configuration
```bash
# Gmail for development
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=dev@yourcompany.com
SMTP_PASSWORD="your-app-password"
FROM_EMAIL=dev@yourcompany.com
FROM_NAME=YourApp Dev
```

### Testing Configuration
```bash
# No SMTP - development mode
# SMTP_USERNAME=
# SMTP_PASSWORD=
FROM_EMAIL=test@yourcompany.com
FROM_NAME=YourApp Test
```

## Monitoring and Logging

### Log Messages
- `🔥 EMAIL: Password reset email sent successfully`
- `⚠️ NO SMTP CREDENTIALS CONFIGURED`
- `SMTP email sending failed: [error details]`

### Monitoring Points
- Email send success/failure rates
- SMTP connection health
- Template rendering performance
- User email engagement

## API Reference

### EmailService Class

#### Constructor
```python
EmailService()
```
Initializes the email service with environment configuration.

#### send_password_reset_email()
```python
send_password_reset_email(
    to_email: str, 
    reset_link: str, 
    user_name: Optional[str] = None
) -> bool
```

**Parameters:**
- `to_email`: Recipient email address
- `reset_link`: Password reset URL from Firebase
- `user_name`: Optional display name for personalization

**Returns:**
- `bool`: True if email was sent successfully

**Example:**
```python
success = email_service.send_password_reset_email(
    to_email="user@example.com",
    reset_link="https://app.com/reset/abc123",
    user_name="John Doe"
)
```