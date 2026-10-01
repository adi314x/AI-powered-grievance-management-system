"""
Centralized email service with standardized templates and link generation.
Supports: Gmail SMTP, Formspree API, and console fallback.
"""

from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠ 'requests' library not installed. Run: pip install requests")

from backend.config import Config


class EmailService:
    FORMSPREE_ENDPOINT = os.environ.get('FORMSPREE_ENDPOINT', '')
    TEMPLATE_DIVIDER = '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

    @staticmethod
    def app_base_url():
        """Return canonical app base URL for links included in emails."""
        return (Config.APP_BASE_URL or 'http://localhost:8000').rstrip('/')

    @staticmethod
    def build_app_url(path, query_params=None):
        """Build absolute app URL using APP_BASE_URL."""
        normalized_path = path if path.startswith('/') else f'/{path}'
        url = f"{EmailService.app_base_url()}{normalized_path}"
        if query_params:
            url = f"{url}?{urlencode(query_params)}"
        return url

    @staticmethod
    def tracking_url(grievance_id):
        return EmailService.build_app_url('/track.html', {'id': grievance_id})

    @staticmethod
    def login_url():
        return EmailService.build_app_url('/login.html')

    @staticmethod
    def officer_portal_url():
        return EmailService.build_app_url('/officer.html')

    @staticmethod
    def _normalize_text(value):
        if value is None:
            return ''
        return str(value).strip()

    @staticmethod
    def _render_template(recipient_name, intro=None, sections=None, action_label=None, action_url=None, closing=None):
        greeting_name = EmailService._normalize_text(recipient_name) or 'User'
        lines = [f"Dear {greeting_name},", '']

        intro_text = EmailService._normalize_text(intro)
        if intro_text:
            lines.append(intro_text)
            lines.append('')

        for title, content in (sections or []):
            content_text = EmailService._normalize_text(content)
            if not content_text:
                continue
            lines.extend([
                EmailService.TEMPLATE_DIVIDER,
                title,
                EmailService.TEMPLATE_DIVIDER,
                content_text,
                ''
            ])

        if action_url:
            lines.extend([
                EmailService.TEMPLATE_DIVIDER,
                action_label or '🔗 VIEW DETAILS',
                EmailService.TEMPLATE_DIVIDER,
                action_url,
                ''
            ])

        closing_text = EmailService._normalize_text(closing)
        if closing_text:
            lines.append(closing_text)
            lines.append('')

        lines.extend([
            '---',
            'This is an automated message. Please do not reply.',
            'Smart Grievance System | Digital India Initiative 🇮🇳'
        ])
        return '\n'.join(lines)

    @staticmethod
    def send_via_gmail(to_email, subject, body):
        """Send email via Gmail SMTP."""
        try:
            if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
                return False

            msg = MIMEMultipart('alternative')
            msg['From'] = Config.MAIL_DEFAULT_SENDER
            msg['To'] = to_email
            msg['Subject'] = subject

            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 640px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <div style="background: linear-gradient(135deg, #2563eb, #1e40af); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                            <h2 style="margin: 0;">🇮🇳 Smart Grievance System</h2>
                        </div>
                        <div style="padding: 20px; background: #f9fafb;">
                            <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{body}</pre>
                        </div>
                    </div>
                </body>
            </html>
            """

            part_plain = MIMEText(body, 'plain')
            part_html = MIMEText(html_body, 'html')
            msg.attach(part_plain)
            msg.attach(part_html)

            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)

            print(f"✓ Email sent via Gmail to {to_email}")
            return True
        except Exception as error:
            print(f"⚠ Gmail SMTP failed: {error}")
            return False

    @staticmethod
    def send_via_formspree(to_email, subject, body):
        """Send email via Formspree API."""
        if not REQUESTS_AVAILABLE or not EmailService.FORMSPREE_ENDPOINT:
            return False

        try:
            response = requests.post(
                EmailService.FORMSPREE_ENDPOINT,
                data={
                    'email': to_email,
                    'subject': subject,
                    'message': body,
                    '_replyto': to_email,
                    '_subject': subject,
                    '_template': 'table',
                },
                headers={'Accept': 'application/json'},
                timeout=10,
            )
            if response.status_code == 200:
                print(f"✓ Email sent via Formspree to {to_email}")
                return True
            print(f"⚠ Formspree API error: {response.status_code} - {response.text}")
            return False
        except Exception as error:
            print(f"⚠ Formspree failed: {error}")
            return False

    @staticmethod
    def send_to_console(to_email, subject, body):
        """Fallback: print email content to console."""
        print(f"\n{'=' * 70}")
        print('📧 [EMAIL NOTIFICATION]')
        print(f"{'=' * 70}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"{'=' * 70}")
        print(body)
        print(f"{'=' * 70}\n")
        return True

    @staticmethod
    def send_email(to_email, subject, body):
        """Smart email dispatch with fallbacks."""
        if Config.DEMO_EMAIL_MODE:
            return EmailService.send_to_console(to_email, subject, body)

        if Config.MAIL_USERNAME and Config.MAIL_PASSWORD and EmailService.send_via_gmail(to_email, subject, body):
            return True

        if EmailService.FORMSPREE_ENDPOINT and EmailService.send_via_formspree(to_email, subject, body):
            return True

        # In development, keep console fallback for local debugging.
        if not Config.IS_PRODUCTION:
            return EmailService.send_to_console(to_email, subject, body)

        print("⚠ Email delivery skipped: no configured SMTP/Formspree provider in production mode")
        return False

    @staticmethod
    def send_otp_email(user_email, otp, user_name=None):
        subject = 'Your OTP for Smart Grievance System Verification'
        body = EmailService._render_template(
            recipient_name=user_name or 'User',
            intro='Thank you for registering with the Smart Grievance System.',
            sections=[
                ('🔐 YOUR VERIFICATION CODE', otp),
                ('⏰ IMPORTANT INFORMATION', '• OTP is valid for 5 minutes\n• Do not share OTP with anyone\n• Ignore if you did not request this'),
                ('🔒 SECURITY TIP', 'Government officials will never ask for your OTP.'),
            ],
        )
        return EmailService.send_email(user_email, subject, body)

    @staticmethod
    def send_welcome_email(user_email, user_name):
        subject = 'Welcome to Smart Grievance System 🇮🇳'
        body = EmailService._render_template(
            recipient_name=user_name,
            intro='Your account has been verified successfully.',
            sections=[
                ('✅ ACCOUNT ACTIVATED', 'You can now submit grievances and track resolution updates.'),
                ('🎯 WHAT YOU CAN DO', '• Submit complaints\n• Track status\n• Receive officer responses\n• Use multilingual interface'),
            ],
            action_label='🔗 LOGIN TO PORTAL',
            action_url=EmailService.login_url(),
        )
        return EmailService.send_email(user_email, subject, body)

    @staticmethod
    def send_password_reset_confirmation(user_email, user_name):
        subject = 'Password Reset Successful - Smart Grievance System'
        body = EmailService._render_template(
            recipient_name=user_name,
            intro='Your account password has been changed successfully.',
            sections=[
                ('✅ PASSWORD CHANGED', f'Changed at {datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")}.')
            ],
            action_label='🔗 LOGIN NOW',
            action_url=EmailService.login_url(),
        )
        return EmailService.send_email(user_email, subject, body)

    @staticmethod
    def send_grievance_notification(user_email, grievance_id, department, status, message):
        subject = f'Grievance #{grievance_id} - Status Update: {status}'
        body = EmailService._render_template(
            recipient_name='Citizen',
            intro='Your grievance has been updated in the system.',
            sections=[
                ('📋 COMPLAINT DETAILS', f'Complaint ID: #{grievance_id}\nDepartment: {department}\nCurrent Status: {status}'),
                ('📝 UPDATE DETAILS', message),
            ],
            action_label='🔗 TRACK YOUR COMPLAINT',
            action_url=EmailService.tracking_url(grievance_id),
        )
        return EmailService.send_email(user_email, subject, body)

    @staticmethod
    def send_officer_assignment_notification(officer_email, officer_name, grievance_id, complaint_text, department, user_name, user_phone):
        subject = f'🚨 New Case Assigned - Grievance #{grievance_id}'
        body = EmailService._render_template(
            recipient_name=officer_name,
            intro='A new grievance has been assigned to you by Admin.',
            sections=[
                ('📋 CASE DETAILS', f'Complaint ID: #{grievance_id}\nDepartment: {department}\nStatus: Assigned to Department'),
                ('👤 COMPLAINANT INFORMATION', f'Name: {user_name}\nPhone: {user_phone}'),
                ('📝 COMPLAINT DESCRIPTION', f"{(complaint_text or '')[:300]}{'...' if complaint_text and len(complaint_text) > 300 else ''}"),
            ],
            action_label='🔗 OFFICER PORTAL',
            action_url=EmailService.officer_portal_url(),
            closing='Please review and update status promptly.',
        )
        return EmailService.send_email(officer_email, subject, body)

    @staticmethod
    def send_status_update_notification(user_email, user_name, grievance_id, old_status, new_status, update_message, department, officer_name):
        subject = f'Status Update: Grievance #{grievance_id} - {new_status}'
        body = EmailService._render_template(
            recipient_name=user_name,
            intro='Your grievance status has changed.',
            sections=[
                ('📊 STATUS CHANGE', f'Complaint ID: #{grievance_id}\nDepartment: {department}\nPrevious: {old_status}\nCurrent: {new_status}'),
                ('👮 OFFICER UPDATE', f'Updated by: {officer_name}\n\n{update_message}'),
            ],
            action_label='🔗 VIEW FULL TIMELINE',
            action_url=EmailService.tracking_url(grievance_id),
        )
        return EmailService.send_email(user_email, subject, body)

    @staticmethod
    def send_citizen_comment_alert(officer_email, officer_name, grievance_id, comment_text, response_hours=24):
        subject = f'🔔 Citizen Comment - Grievance #{grievance_id}'
        body = EmailService._render_template(
            recipient_name=officer_name,
            intro='A citizen has added a new comment on a grievance assigned to your queue.',
            sections=[
                ('💬 CITIZEN COMMENT', f'Complaint ID: #{grievance_id}\n\n"{comment_text}"'),
                ('⏱ RESPONSE WINDOW', f'Please respond within {response_hours} hours to avoid escalation.'),
            ],
            action_label='🔗 VIEW & RESPOND',
            action_url=EmailService.tracking_url(grievance_id),
        )
        return EmailService.send_email(officer_email, subject, body)

    @staticmethod
    def send_officer_reply_alert(citizen_email, citizen_name, grievance_id, officer_name, department, comment_text):
        subject = f'New Response on Your Grievance #{grievance_id}'
        body = EmailService._render_template(
            recipient_name=citizen_name,
            intro=f'{officer_name} from {department} has replied to your grievance.',
            sections=[
                ('💬 OFFICER RESPONSE', f'Complaint ID: #{grievance_id}\n\n"{comment_text}"')
            ],
            action_label='🔗 VIEW & REPLY',
            action_url=EmailService.tracking_url(grievance_id),
        )
        return EmailService.send_email(citizen_email, subject, body)

    @staticmethod
    def send_comment_notification(user_email, grievance_id, commenter_name, comment_text):
        """Backward-compatible generic comment notification."""
        subject = f'New Comment on Grievance #{grievance_id}'
        body = EmailService._render_template(
            recipient_name='User',
            intro=f'{commenter_name} added a new comment.',
            sections=[
                ('💬 COMMENT DETAILS', f'Complaint ID: #{grievance_id}\n\n"{comment_text}"'),
            ],
            action_label='🔗 VIEW COMMENT THREAD',
            action_url=EmailService.tracking_url(grievance_id),
        )
        return EmailService.send_email(user_email, subject, body)

    @staticmethod
    def send_escalation_alert(superior_email, superior_name, grievance_id, current_officer_name, comment_text, comment_sent_at=None, response_deadline=None, escalation_type='auto'):
        subject_prefix = '⚠️ ESCALATED' if escalation_type == 'auto' else '⚠️ MANUAL ESCALATION'
        subject = f'{subject_prefix}: Grievance #{grievance_id}'
        body = EmailService._render_template(
            recipient_name=superior_name,
            intro=f'Citizen comment has been escalated from {current_officer_name}.',
            sections=[
                ('💬 ESCALATED COMMENT', f'Complaint ID: #{grievance_id}\n\n"{comment_text}"'),
                ('🕒 TIMING DETAILS', f'Comment sent: {comment_sent_at or "N/A"}\nResponse deadline: {response_deadline or "N/A"}'),
            ],
            action_label='🔗 REVIEW GRIEVANCE',
            action_url=EmailService.tracking_url(grievance_id),
        )
        return EmailService.send_email(superior_email, subject, body)

    @staticmethod
    def send_escalation_notice_to_officer(officer_email, officer_name, grievance_id, escalated_to_name):
        subject = f'⚠️ Escalation Notice - Grievance #{grievance_id}'
        body = EmailService._render_template(
            recipient_name=officer_name,
            intro=f'Your grievance comment thread has been escalated to {escalated_to_name}.',
            sections=[
                ('📌 ACTION REQUIRED', 'Coordinate with the escalated officer/admin and respond to the citizen promptly.')
            ],
            action_label='🔗 OPEN GRIEVANCE',
            action_url=EmailService.tracking_url(grievance_id),
        )
        return EmailService.send_email(officer_email, subject, body)

    @staticmethod
    def send_fraud_report_alert(admin_email, admin_name, grievance_id, officer_name, fraud_type, description):
        subject = f'Fraud Review Needed - Grievance #{grievance_id}'
        body = EmailService._render_template(
            recipient_name=admin_name,
            intro='An officer has submitted a fraud report that requires admin review.',
            sections=[
                ('🚩 FRAUD REPORT SUMMARY', f'Complaint ID: #{grievance_id}\nReported by: {officer_name}\nType: {fraud_type}'),
                ('📝 OFFICER NOTES', description),
            ],
            action_label='🔗 REVIEW CASE',
            action_url=EmailService.tracking_url(grievance_id),
        )
        return EmailService.send_email(admin_email, subject, body)

    @staticmethod
    def send_fraud_review_notice(citizen_email, citizen_name, grievance_id, stage, details=None):
        stage_map = {
            'under_review': ('Complaint Under Verification', 'Your complaint is currently under fraud verification by admin.'),
            'dismissed': ('Fraud Report Dismissed', 'The fraud report on your complaint has been dismissed.'),
        }
        title, intro = stage_map.get(stage, ('Fraud Review Update', 'There is an update on your complaint review status.'))
        subject = f'{title} - Grievance #{grievance_id}'
        body = EmailService._render_template(
            recipient_name=citizen_name,
            intro=intro,
            sections=[('📋 REVIEW DETAILS', details or f'Complaint ID: #{grievance_id}')],
            action_label='🔗 VIEW CASE STATUS',
            action_url=EmailService.tracking_url(grievance_id),
        )
        return EmailService.send_email(citizen_email, subject, body)

    @staticmethod
    def send_account_warning_email(citizen_email, citizen_name, grievance_id, warning_count, reason=None):
        subject = f'Warning Issued - Grievance #{grievance_id}'
        body = EmailService._render_template(
            recipient_name=citizen_name,
            intro='A fraud complaint against your grievance has been verified.',
            sections=[
                ('⚠️ WARNING STATUS', f'Warning count: {warning_count}\nComplaint ID: #{grievance_id}'),
                ('📝 REASON', reason or 'Repeated fraudulent complaint activity detected.'),
            ],
            action_label='🔗 VIEW COMPLAINT',
            action_url=EmailService.tracking_url(grievance_id),
        )
        return EmailService.send_email(citizen_email, subject, body)

    @staticmethod
    def send_account_suspension_email(citizen_email, citizen_name, reason, grievance_id=None):
        subject = 'Account Suspended - Smart Grievance System'
        details = reason or 'Your account has been suspended due to policy violations.'
        if grievance_id:
            details = f'{details}\nRelated complaint: #{grievance_id}'
        body = EmailService._render_template(
            recipient_name=citizen_name,
            intro='Your account has been suspended after admin fraud review.',
            sections=[('⛔ SUSPENSION DETAILS', details)],
            action_label='🔗 LOGIN PORTAL',
            action_url=EmailService.login_url(),
        )
        return EmailService.send_email(citizen_email, subject, body)
