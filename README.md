NSS BloodLink – Smart Blood Donation Network

NSS BloodLink is a real-time blood donation coordination platform that connects hospitals with nearby eligible blood donors. The system automatically detects donors based on live geolocation, availability, and blood compatibility, and allows hospitals to notify donors instantly via email.

🚀 Key Features
Feature	Description
Donor Registration	Donors register with blood type & location.
Real-time Availability	Donor online/offline status is tracked through Redis GEO.
Nearby Donor Matching	Hospital requests automatically find closest eligible donors.
Emergency Notification	Hospitals can notify donors with one click, emails are sent instantly.
Web Dashboard	Admin UI for monitoring requests, donors, and hospitals.
Socket.IO Live Updates	New requests and donor status push updates without refresh.

🧱 System Architecture
Frontend (React + Vite) 
        ↓ REST / WebSocket
Backend (FastAPI + Socket.IO)
        ↓ SQLAlchemy ORM
PostgreSQL (Donor & Hospital Data)
        ↓ Redis GEO + Cache
Redis (Live Location & Availability)
        ↓
SendGrid (Email Notifications)

📍 How the Workflow Works
1) Donor Registration

Donor signs up → stored in PostgreSQL.

Their coordinates (lat, lng) also stored in Redis GEO index.

2) Hospital Creates Blood Request

Hospital enters required blood type & urgency.

Request is broadcast live to all staff dashboards via Socket.IO.

3) Finding Nearby Donors

When user clicks Notify Donors:

GET /donors/nearby?lat=<hospital_lat>&lng=<hospital_lng>&km=5&blood_group=O+


This returns a list sorted by distance + recent activity.

4) Notifying Donors

The frontend sends the list to:

POST /donors/notify


Backend loops through donors → sends personalized email via SendGrid:

Dear <name>, A nearby hospital urgently needs <blood_group>. Please help.

✅ Technologies Used
Layer	Technology
Frontend	React, Vite, TailwindCSS, Framer Motion, ShadCN UI
Backend	FastAPI, SQLAlchemy, Socket.IO
Database	PostgreSQL
Cache/Geo Index	Redis
Email Service	SendGrid
Deployment Ready For	Railway / Render / Vercel / Docker
🛠 Local Setup
1) Clone the Project
git clone https://github.com/<your-repo>/NSS-Bloodlink.git
cd NSS-Bloodlink

2) Backend Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


Create .env:

DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/nss_blood
REDIS_URL=redis://localhost:6379
SENDGRID_API_KEY=SG.xxxxxx
EMAIL_FROM=your_email@gmail.com
FRONTEND_URL=http://localhost:5173


Start backend:

uvicorn app.main:app --reload

3) Redis Setup

Mac:

brew install redis
redis-server

4) Frontend Setup
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev

🔔 Notify Donors API Example
Request
await fetch("http://localhost:8000/donors/notify", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(nearbyDonors),
});

Response
{
  "status": "ok",
  "notified": 5
}

🎯 Future Enhancements

SMS & Whatsapp Notifications (Twilio)
ML-based donor scoring
Live navigation directions to donation centers

