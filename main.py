from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3
import qrcode
import smtplib
from email.message import EmailMessage
import os

app = FastAPI()

# ✅ CORS Middleware to Fix Fetch Errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Connect to SQLite Database
def get_db():
    conn = sqlite3.connect("data.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                 (bill_no TEXT, name TEXT, college_name TEXT, email TEXT, qr_path TEXT)''')
    return conn

# ✅ Pydantic Model for Input Data
class QRRequest(BaseModel):
    bill_no: str
    name: str
    college_name: str
    email: EmailStr

# ✅ Generate and Store QR Code
@app.post("/generate_qr/")
async def generate_qr_code(data: QRRequest):
    try:
        # 1️⃣ Generate QR Code
        filename = f"incognito_{data.bill_no}_{data.name}.png"
        qr_path = os.path.join("qrcodes", filename)

        if not os.path.exists("qrcodes"):
            os.makedirs("qrcodes")

        qr = qrcode.make(f"Bill No: {data.bill_no}\nName: {data.name}\nCollege: {data.college_name}\nEmail: {data.email}")
        qr.save(qr_path)

        # 2️⃣ Store Data in Database
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (data.bill_no, data.name, data.college_name, data.email, qr_path))
        db.commit()
        db.close()

        # 3️⃣ Send QR Code via Email
        send_email(data.email, qr_path)

        return {"message": "QR Code generated and sent to email", "qr_path": qr_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Function to Send Email
def send_email(to_email, qr_path):
    sender_email = "harshithsham8899@gmail.com"  # 🔴 Change this
    sender_password = "dxkc gqef wqny qszp"  # 🔴 Change this (Use App Password for security)

    msg = EmailMessage()
    msg["Subject"] = "Your QR Code"
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content("Here is your generated QR code.")

    # Attach QR Code
    with open(qr_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="image", subtype="png", filename=os.path.basename(qr_path))

    # Send Email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)
