# NSS BloodLink — Smart Blood Donation Network

Real-time blood donation coordination that connects hospitals with nearby, eligible donors.

## Why
- Manual, slow donor tracking and emergency response. *(see deck: Problem, p.2)*  
- No central channel between coordinators and verified donors.  
- Engagement drops after camps.  

## What
- **Donor registration** with blood type & geo.
- **Live availability & location** (Redis GEO + cache).
- **Nearby matching** by distance, compatibility, and recent activity.
- **One-click notifications** to donors (SendGrid email; Socket.IO live updates).
- **Web dashboard** for hospitals/admins.
- **Realtime updates** via REST + WebSocket.

## System Architecture

Frontend (React + Vite + Tailwind + (optional) Framer Motion / ShadCN)
│ REST + WebSocket (Socket.IO)
Backend (FastAPI + SQLAlchemy + python-socketio)
│
PostgreSQL (donors/hospitals) ─ Redis (GEO + cache)
│
Email (SendGrid) • Push/Realtime (Socket.IO; optional FCM)



> *Deck adds optional modules used in pilots: Leaflet maps, Firebase Auth/Firestore, FCM push; Docker/Compose + Makefile for DevOps; AI hooks via LangChain/OpenAI for planning.* *(see deck: Tech Stack, p.4; Workflow, p.5)*

## Features
- Nearby donor search: `GET /donors/nearby?lat=<lat>&lng=<lng>&km=5&blood_group=O+`
- Instant outreach: `POST /donors/notify` (bulk, personalized email)
- Socket-driven dashboards (no refresh)
- Admin insights (requests, donors, hospitals)

## Quickstart

### 1) Clone
```bash
git clone https://github.com/<OWNER>/NSS-BloodLink.git
cd NSS-BloodLink

cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

Create .env:
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/nss_blood
REDIS_URL=redis://localhost:6379
SENDGRID_API_KEY=SG.xxxxxx
EMAIL_FROM=your_email@gmail.com
FRONTEND_URL=http://localhost:5173

# optional (if using Firebase/FCM)
FIREBASE_PROJECT_ID=...
FIREBASE_CLIENT_EMAIL=...
FIREBASE_PRIVATE_KEY="..."

uvicorn app.main:app --reload

# macOS
brew install redis
redis-server

4) Frontend
cd ../frontend
rm -rf node_modules package-lock.json
npm install
npm run dev

(Optional) Docker

# if docker-compose.yml is present
docker compose up --build

API — Notify Donors

Request

await fetch("http://localhost:8000/donors/notify", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(nearbyDonors),
});

Response

{ "status": "ok", "notified": 5 }

Security & Privacy

    Compatibility rules enforced server-side.

    Rate-limited notifications.

    Privacy-preserving IDs (e.g., hashed last-4 Aadhaar when applicable). (see deck: Core Innovations, p.6)

    CORS locked to FRONTEND_URL. Secrets via .env.

Deployment

    Works on Railway, Render, Vercel (frontend), or Docker.

    Modular, low-cost stack, cloud or on-prem. (see deck: Sustainability & Scale, p.7)

Roadmap

    SMS/WhatsApp (Twilio), ML-based donor scoring, live navigation.

    Mobile apps (iOS/Android) with offline + one-tap confirm.

    Advanced dashboards (KPIs, A/B tests, explainability), multi-tenant rollout, cost-aware redistribution, localized messaging, partner onboarding playbook. (see deck: Core/Future, p.6–8)

Screens

    Coordinator login, donor list, AI assistant, camps view, map with donor pins. (see deck: Workflow, p.5)
