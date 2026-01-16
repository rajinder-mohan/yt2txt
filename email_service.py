import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Email configuration from environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_text: Plain text email body
        body_html: Optional HTML email body
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("Warning: SMTP credentials not configured. Email not sent.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add text and HTML parts
        text_part = MIMEText(body_text, 'plain')
        msg.attach(text_part)
        
        if body_html:
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def send_channel_processing_results(
    to_email: str,
    channel_url: str,
    channel_name: Optional[str],
    total_videos: int,
    success_count: int,
    failed_count: int,
    video_results: List[dict]
) -> bool:
    """
    Send email with channel processing results.
    
    Args:
        to_email: Recipient email address
        channel_url: YouTube channel URL
        channel_name: Channel name
        total_videos: Total number of videos processed
        success_count: Number of successful transcriptions
        failed_count: Number of failed transcriptions
        video_results: List of video processing results
    
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = f"YouTube Channel Processing Complete: {channel_name or 'Channel'}"
    
    # Create text body
    text_body = f"""
YouTube Channel Processing Results

Channel: {channel_name or channel_url}
Channel URL: {channel_url}

Summary:
- Total Videos: {total_videos}
- Successful: {success_count}
- Failed: {failed_count}

"""
    
    # Add video details
    if video_results:
        text_body += "Video Details:\n"
        text_body += "-" * 80 + "\n"
        for video in video_results:
            status = video.get('status', 'unknown')
            video_id = video.get('video_id', 'N/A')
            video_url = video.get('video_url', f'https://www.youtube.com/watch?v={video_id}')
            title = video.get('title', 'N/A')
            error = video.get('error', '')
            
            text_body += f"\nVideo ID: {video_id}\n"
            text_body += f"Title: {title}\n"
            text_body += f"URL: {video_url}\n"
            text_body += f"Status: {status}\n"
            if error:
                text_body += f"Error: {error}\n"
            if status == 'success' and video.get('transcript'):
                transcript_preview = video.get('transcript', '')[:200]
                text_body += f"Transcript Preview: {transcript_preview}...\n"
            text_body += "-" * 80 + "\n"
    
    # Create HTML body
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #667eea; color: white; padding: 20px; }}
            .content {{ padding: 20px; }}
            .summary {{ background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .summary-item {{ margin: 10px 0; }}
            .success {{ color: #28a745; font-weight: bold; }}
            .failed {{ color: #dc3545; font-weight: bold; }}
            .video-item {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .video-title {{ font-weight: bold; color: #667eea; }}
            .error {{ color: #dc3545; }}
            .transcript-preview {{ background-color: #f8f9fa; padding: 10px; margin-top: 10px; border-left: 3px solid #667eea; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>YouTube Channel Processing Complete</h1>
        </div>
        <div class="content">
            <h2>Channel Information</h2>
            <p><strong>Channel:</strong> {channel_name or channel_url}</p>
            <p><strong>Channel URL:</strong> <a href="{channel_url}">{channel_url}</a></p>
            
            <div class="summary">
                <h3>Summary</h3>
                <div class="summary-item">Total Videos: <strong>{total_videos}</strong></div>
                <div class="summary-item">Successful: <span class="success">{success_count}</span></div>
                <div class="summary-item">Failed: <span class="failed">{failed_count}</span></div>
            </div>
            
            <h2>Video Details</h2>
    """
    
    if video_results:
        for video in video_results:
            status = video.get('status', 'unknown')
            video_id = video.get('video_id', 'N/A')
            video_url = video.get('video_url', f'https://www.youtube.com/watch?v={video_id}')
            title = video.get('title', 'N/A')
            error = video.get('error', '')
            transcript = video.get('transcript', '')
            
            status_class = 'success' if status == 'success' else 'failed'
            
            html_body += f"""
            <div class="video-item">
                <div class="video-title">{title}</div>
                <p><strong>Video ID:</strong> {video_id}</p>
                <p><strong>URL:</strong> <a href="{video_url}" target="_blank">{video_url}</a></p>
                <p><strong>Status:</strong> <span class="{status_class}">{status}</span></p>
            """
            
            if error:
                html_body += f'<p class="error"><strong>Error:</strong> {error}</p>'
            
            if status == 'success' and transcript:
                transcript_preview = transcript[:500] + ('...' if len(transcript) > 500 else '')
                html_body += f'''
                <div class="transcript-preview">
                    <strong>Transcript Preview:</strong><br>
                    {transcript_preview}
                </div>
                '''
            
            html_body += "</div>"
    
    html_body += """
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, text_body, html_body)
