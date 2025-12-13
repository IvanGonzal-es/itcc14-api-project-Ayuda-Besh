# lib/email_service.py

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

def send_verification_email(to_email: str, verification_code: str, user_name: str = None) -> bool:
    """
    Send verification code via email using SMTP
    
    Returns True if sent successfully, False otherwise
    """
    try:
        # Get SMTP configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        from_email = os.getenv('SMTP_FROM_EMAIL', smtp_username)
        from_name = os.getenv('SMTP_FROM_NAME', 'AyudaBesh')
        
        # If no SMTP credentials configured, return False (will fallback to console)
        if not smtp_username or not smtp_password:
            print(f"[WARNING] SMTP not configured. Verification code for {to_email}: {verification_code}")
            print("   To enable email sending, set SMTP_USERNAME and SMTP_PASSWORD in .env file")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'AyudaBesh - Password Reset Verification Code'
        msg['From'] = formataddr((from_name, from_email))
        msg['To'] = to_email
        
        # Create email body
        user_greeting = f"Hello {user_name}," if user_name else "Hello,"
        
        text_content = f"""
{user_greeting}

You requested to reset your password for your AyudaBesh account.

Your verification code is: {verification_code}

This code will expire in 15 minutes.

If you did not request this password reset, please ignore this email.

Best regards,
AyudaBesh Team
        """
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #0070f3; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
        .code-box {{ background: white; border: 2px solid #0070f3; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
        .code {{ font-size: 32px; font-weight: bold; color: #0070f3; letter-spacing: 5px; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AyudaBesh</h1>
        </div>
        <div class="content">
            <p>{user_greeting}</p>
            <p>You requested to reset your password for your AyudaBesh account.</p>
            
            <div class="code-box">
                <p style="margin: 0 0 10px 0; color: #666;">Your verification code is:</p>
                <div class="code">{verification_code}</div>
            </div>
            
            <p>This code will expire in <strong>15 minutes</strong>.</p>
            
            <p>If you did not request this password reset, please ignore this email.</p>
            
            <div class="footer">
                <p>Best regards,<br>AyudaBesh Team</p>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Enable encryption
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print(f"[OK] Verification email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_email}: {e}")
        print(f"   Verification code: {verification_code} (fallback)")
        return False

def send_sms_verification(phone_number: str, verification_code: str) -> bool:
    """
    Send verification code via SMS
    
    For now, this is a placeholder. To implement SMS:
    - Use Twilio API
    - Use AWS SNS
    - Use other SMS service
    
    Returns True if sent successfully, False otherwise
    """
    try:
        # Check if Twilio is configured
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        twilio_phone = os.getenv('TWILIO_PHONE_NUMBER', '')
        
        if twilio_account_sid and twilio_auth_token and twilio_phone:
            # Try to use Twilio if available
            try:
                from twilio.rest import Client
                client = Client(twilio_account_sid, twilio_auth_token)
                message = client.messages.create(
                    body=f'Your AyudaBesh verification code is: {verification_code}. Valid for 15 minutes.',
                    from_=twilio_phone,
                    to=phone_number
                )
                print(f"[OK] SMS sent successfully to {phone_number}")
                return True
            except ImportError:
                print("[WARNING] Twilio not installed. Install with: pip install twilio")
            except Exception as e:
                print(f"[ERROR] Twilio SMS failed: {e}")
        
        # Fallback: print to console
        print(f"[WARNING] SMS not configured. Verification code for {phone_number}: {verification_code}")
        print("   To enable SMS, set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env")
        print("   Or install twilio: pip install twilio")
        return False
        
    except Exception as e:
        print(f"[ERROR] Failed to send SMS to {phone_number}: {e}")
        print(f"   Verification code: {verification_code} (fallback)")
        return False
