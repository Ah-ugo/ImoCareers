import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

async def send_email(to_email: str, subject: str, html_content: str):
    message = MIMEMultipart("alternative")
    message["From"] = os.getenv("SMTP_USERNAME")
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(html_content, "html"))

    try:
        await aiosmtplib.send(
            message,
            hostname=os.getenv("SMTP_HOST"),
            port=int(os.getenv("SMTP_PORT")),
            username=os.getenv("SMTP_USERNAME"),
            password=os.getenv("SMTP_PASSWORD"),
            use_tls=True
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


async def send_welcome_email(email: str, name: str):
    subject = "Welcome to Imo Career Hub!"
    html_content = f"""
    <html>
        <body>
            <h2>Welcome to Imo Career Hub, {name}!</h2>
            <p>Thank you for joining our platform. We're excited to help you find your perfect career opportunity.</p>
            <p>Get started by:</p>
            <ul>
                <li>Completing your profile</li>
                <li>Uploading your CV</li>
                <li>Browsing available jobs</li>
            </ul>
            <p>Best regards,<br>The Imo Career Hub Team</p>
        </body>
    </html>
    """
    return await send_email(email, subject, html_content)


async def send_job_alert(email: str, job_matches: list):
    subject = "New Job Matches Found!"
    html_content = f"""
    <html>
        <body>
            <h2>New Job Opportunities</h2>
            <p>We found some new jobs that match your profile:</p>
            <ul>
                {''.join(f'<li>{job["title"]} at {job["company"]}</li>' for job in job_matches)}
            </ul>
            <p>Log in to your account to view full details and apply.</p>
        </body>
    </html>
    """
    return await send_email(email, subject, html_content)