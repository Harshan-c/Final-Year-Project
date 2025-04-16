import smtplib
from email.message import EmailMessage

sender_email = "harshithsham8899@gmail.com"
sender_password = "dxkc gqef wqny qszp"
receiver_email = "kavyamurthy2004@gmail.com"

msg = EmailMessage()
msg["Subject"] = "Test Email"
msg["From"] = sender_email
msg["To"] = receiver_email
msg.set_content("hii putti.")

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)
    print("Email sent successfully!")
except Exception as e:
    print("Error sending email:", e)
