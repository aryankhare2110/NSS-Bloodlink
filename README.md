# NSS BloodLink — AI-powered Blood Donation Platform

## Overview

NSS BloodLink is an intelligent blood donation management platform that connects donors with hospitals in need. The platform uses AI and Machine Learning to predict blood shortages, optimize inventory redistribution, and alert volunteers proactively.

## Key Features

### 🤖 AI-Powered Donor Matching
- Natural language processing for donor queries
- Intelligent location-based donor recommendations
- Real-time donor availability tracking

### 📊 ML-Based Demand Forecasting
- **Predictive Analytics**: Forecasts blood demand 24-48 hours ahead
- **Seasonal Pattern Detection**: Identifies spikes after rainy season (dengue/malaria)
- **Risk Assessment**: Critical, High, Medium, Low risk levels
- **Auto-Alerting**: Notifies volunteers before shortages occur

### 🔄 Intelligent Redistribution
- Identifies surplus and shortage hospitals
- Priority-based matching algorithm
- Forecast-driven redistribution planning
- Real-time inventory management

### 🚨 Real-Time Communications
- WebSocket-based live updates
- Instant shortage alerts
- Volunteer notification system

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **scikit-learn** - ML forecasting model
- **pandas & numpy** - Data processing
- **LangChain & OpenAI** - AI chat capabilities
- **Socket.IO** - Real-time communications

### Machine Learning
- **Random Forest Regressor** for demand prediction
- Seasonal pattern recognition
- Historical data analysis
- Confidence scoring

## Quick Start

### Prerequisites
- Python 3.10+
- pip
- SQLite (included) or PostgreSQL

### Installation

1. Clone the repository:
```bash
git clone https://github.com/aryankhare2110/NSS-Bloodlink.git
cd NSS-Bloodlink/backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize database:
```bash
python seed.py
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

6. Access the API documentation:
```
http://localhost:8000/docs
```

## Blood Demand Forecasting

### Training the Model

Train the ML model on historical data:
```bash
curl -X POST http://localhost:8000/forecasting/train
```

### Generating Forecasts

Generate 48-hour demand forecasts:
```bash
curl -X POST http://localhost:8000/forecasting/generate \
  -H "Content-Type: application/json" \
  -d '{"hours_ahead": 48}'
```

### Sending Alerts

Alert volunteers about predicted shortages:
```bash
curl -X POST http://localhost:8000/forecasting/alerts/send \
  -H "Content-Type: application/json" \
  -d '{"min_risk_level": "High"}'
```

### Redistribution Planning

Get forecast-based redistribution recommendations:
```bash
curl -X POST http://localhost:8000/forecasting/redistribution/forecast-based?threshold_risk=High
```

For detailed forecasting documentation, see [Forecasting Guide](docs/forecasting_guide.md).

## Demo Script

Run the complete forecasting workflow demo:
```bash
cd backend
python examples/forecasting_demo.py
```

## API Endpoints

### Donors (`/donors`)
- `GET /donors` - List all donors
- `POST /donors` - Register new donor
- `GET /donors/{id}` - Get donor details
- `PUT /donors/{id}` - Update donor
- `DELETE /donors/{id}` - Remove donor

### Requests (`/requests`)
- `GET /requests` - List blood requests
- `POST /requests` - Create new request
- `PUT /requests/{id}/status` - Update request status

### AI Chat (`/ai`)
- `POST /ai/chat` - Chat with AI assistant
- `GET /ai/recommend-location` - Get camp location recommendations

### Forecasting (`/forecasting`)
- `POST /forecasting/train` - Train ML model
- `POST /forecasting/generate` - Generate forecasts
- `GET /forecasting/forecasts` - Retrieve forecasts
- `POST /forecasting/alerts/send` - Send alerts
- `GET /forecasting/inventory` - View inventory
- `GET /forecasting/redistribution/opportunities` - Find redistribution matches
- `POST /forecasting/redistribution/execute` - Execute transfer

Full API documentation available at `/docs` endpoint.

## How It Works

### Demand Forecasting Flow

1. **Data Collection**: Historical demand data (seasonal patterns, disease outbreaks)
2. **Model Training**: Random Forest model learns patterns
3. **Prediction**: Forecasts demand 24-48 hours ahead
4. **Risk Assessment**: Evaluates shortage risk levels
5. **Alerting**: Notifies volunteers of high-risk situations
6. **Redistribution**: Plans optimal blood transfers

### Seasonal Intelligence

The system recognizes seasonal patterns:
- **Winter** (Dec-Feb): Baseline demand
- **Summer** (Mar-May): Slightly reduced
- **Monsoon** (Jun-Sep): Increased (1.3x) - accidents, diseases
- **Post-Monsoon** (Oct-Nov): Peak (1.8x) - dengue/malaria spike

### Risk Levels

- **Critical**: <1 day supply - Immediate action required
- **High**: 1-2 days supply - Alert volunteers
- **Medium**: 2-3 days supply - Monitor closely
- **Low**: 3+ days supply - Normal operations

## Project Structure

```
NSS-Bloodlink/
├── backend/
│   ├── app/
│   │   ├── ai/              # AI chat functionality
│   │   ├── database/        # Database configuration
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routes/          # API endpoints
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   │       ├── forecasting.py      # ML forecasting
│   │       └── redistribution.py   # Redistribution logic
│   ├── examples/            # Demo scripts
│   └── seed.py             # Database seeding
├── docs/                   # Documentation
│   └── forecasting_guide.md
└── frontend/              # Frontend application
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Support

For questions or support, please open an issue on GitHub.

