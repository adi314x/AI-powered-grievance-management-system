import random
from datetime import datetime, timedelta
from backend.models import OTPRequest, User
from backend.extensions import db
from backend.config import Config
from backend.services.email_service import EmailService

class OTPService:
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return random.randint(100000, 999999)
    
    @staticmethod
    def create_otp_request(identifier, channel='email'):
        """
        Create an OTP request
        identifier: email or phone
        channel: 'email' or 'phone'
        """
        if channel == 'phone' and not Config.DEMO_SMS_MODE:
            return None, "Phone OTP delivery is not configured for this environment."

        # Check rate limit
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_requests = OTPRequest.query.filter(
            OTPRequest.identifier == identifier,
            OTPRequest.created_at >= one_hour_ago
        ).count()
        
        if recent_requests >= Config.OTP_RATE_LIMIT_PER_HOUR:
            return None, "Too many OTP requests. Please try again later."
        
        # Generate OTP
        otp = OTPService.generate_otp()
        
        # Create OTP request
        otp_request = OTPRequest(
            identifier=identifier,
            channel=channel,
            expires_at=datetime.utcnow() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
        )
        otp_request.set_otp(otp)
        
        db.session.add(otp_request)
        db.session.commit()

        # In explicit demo mode, print OTP to console for manual testing.
        if channel == 'phone' and Config.DEMO_SMS_MODE:
            print(f"\n{'='*60}")
            print(f"[DEMO SMS MODE] OTP for {identifier} ({channel})")
            print(f"OTP: {otp}")
            print(f"Expires at: {otp_request.expires_at}")
            print(f"{'='*60}\n")
        
        # Send OTP via email if channel is email
        if channel == 'email':
            try:
                # Try to get user name
                user = User.query.filter_by(email=identifier).first()
                user_name = user.name if user else None
                
                # Send OTP email (must succeed in non-demo email mode).
                email_sent = EmailService.send_otp_email(identifier, str(otp), user_name)
                if not email_sent:
                    db.session.delete(otp_request)
                    db.session.commit()
                    return None, "Failed to send OTP email. Please try again later."
            except Exception as e:
                print(f"⚠️ Failed to send OTP email: {e}")
                db.session.delete(otp_request)
                db.session.commit()
                return None, "Failed to send OTP email. Please try again later."
        
        return otp, None
    
    @staticmethod
    def verify_otp(identifier, otp):
        """
        Verify OTP
        Returns: (success: bool, message: str)
        """
        # Find the most recent OTP request
        otp_request = OTPRequest.query.filter_by(
            identifier=identifier
        ).order_by(OTPRequest.created_at.desc()).first()
        
        if not otp_request:
            return False, "No OTP request found"
        
        # Check if expired
        if datetime.utcnow() > otp_request.expires_at:
            return False, "OTP has expired"
        
        # Check attempts
        if otp_request.attempts >= Config.OTP_MAX_ATTEMPTS:
            return False, "Maximum verification attempts exceeded"
        
        # Increment attempts
        otp_request.attempts += 1
        db.session.commit()
        
        # Verify OTP
        if otp_request.check_otp(otp):
            return True, "OTP verified successfully"
        else:
            return False, f"Invalid OTP. {Config.OTP_MAX_ATTEMPTS - otp_request.attempts} attempts remaining"
