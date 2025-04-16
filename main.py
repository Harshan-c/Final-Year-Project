from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uuid, os, qrcode, smtplib
from email.message import EmailMessage
from datetime import datetime
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Firebase initialization
cred = credentials.Certificate("serviceAccountKey.json")
initialize_app(cred)
db = firestore.client()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Data model
class TicketRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str

@app.post("/generate_ticket/")
async def generate_ticket(data: TicketRequest):
    try:
        # Create unique ticket ID
        unique_id = str(uuid.uuid4())

        # Store ticket in Firestore
        db.collection("tickets").document(unique_id).set({
            "unique_id": unique_id,
            "name": data.name,
            "email": data.email,
            "phone": data.phone
        })

        # Create QR code
        qr_dir = "static/qr_codes"
        os.makedirs(qr_dir, exist_ok=True)
        qr_path = os.path.join(qr_dir, f"{unique_id}.png")
        qrcode.make(unique_id).save(qr_path)

        # Send ticket to email
        send_email(data.email, data.name, qr_path)

        return {"message": "Ticket created and sent to email.", "id": unique_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def send_email(to_email, user_name, qr_path):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    current_time = datetime.now().strftime("%B %d, %Y %I:%M %p")

    msg = EmailMessage()
    msg["Subject"] = "Your Ticket | Incognito"
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content("This is your ticket. Open in a browser to view the QR code.")

    html = f"""
    <html>
      <body style="font-family: Arial; background-color: #f4f4f4; padding: 20px;">
        <div style="background-color: #fff; padding: 20px; text-align: center; border-radius: 8px;">
          <h2>Hello {user_name} 👋</h2>
          <p>This is your ticket QR code. Show this at the event.</p>
          <img src="cid:qr_image" width="200" height="200" />
          <p><strong>Date:</strong> {current_time}</p>
          <hr />
          <p style="font-size: 12px; color: gray;">© Incognito 2025 | Auto-generated email</p>
        </div>
      </body>
    </html>
    """
    msg.add_alternative(html, subtype="html")

    with open(qr_path, "rb") as f:
        msg.get_payload()[1].add_related(f.read(), maintype="image", subtype="png", cid="qr_image")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)
