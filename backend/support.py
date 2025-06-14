import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def show_support_form():
    """Display the support form and handle form submission."""
    st.subheader("Contact Support")
    
    with st.form("support_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        subject = st.text_input("Subject")
        message = st.text_area("Message", height=200)
        
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            if not all([name, email, subject, message]):
                st.error("Please fill in all fields")
                return
                
            try:
                # Send email using environment variables
                send_support_email(name, email, subject, message)
                st.success("Thank you for your message! We'll get back to you soon.")
            except Exception as e:
                st.error(f"Failed to send message. Please try again later. Error: {str(e)}")

def send_support_email(name, email, subject, message):
    """Send support email using configured SMTP settings."""
    # Get email configuration from environment variables
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    support_email = os.getenv("SUPPORT_EMAIL", smtp_username)
    
    if not all([smtp_username, smtp_password]):
        raise ValueError("Email configuration is incomplete")
    
    # Create message
    msg = MIMEMultipart()
    msg["From"] = smtp_username
    msg["To"] = support_email
    msg["Subject"] = f"Support Request: {subject}"
    
    # Create email body
    body = f"""
    New support request received:
    
    Name: {name}
    Email: {email}
    Subject: {subject}
    
    Message:
    {message}
    """
    
    msg.attach(MIMEText(body, "plain"))
    
    # Send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg) 