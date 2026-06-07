# Sleep Pattern Clustering & Lifestyle Analytics

A full-stack healthcare analytics platform for sleep pattern analysis, ML clustering, lifestyle correlation, predictive modeling, and personalized recommendations.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Shadcn UI, Plotly |
| Backend | FastAPI, SQLAlchemy, JWT Auth |
| Database | PostgreSQL |
| ML | Scikit-learn, XGBoost, SHAP |
| DevOps | Docker, Docker Compose |

## Features

- **Authentication** — Sign up, login, JWT-secured API
- **Data Upload** — Fitbit CSV, Apple Health XML, Garmin CSV with automatic preprocessing
- **Data Pipeline** — Missing value handling, outlier detection, time normalization, feature engineering
- **Clustering** — K-Means & hierarchical clustering with elbow/silhouette visualizations
- **Dashboard** — PCA plots, radar charts, heatmaps, cluster statistics
- **Lifestyle Analysis** — Correlation matrix, ANOVA, chi-square, feature importance
- **Predictions** — Random Forest & XGBoost classifiers with SHAP explainability
- **Recommendations** — Personalized sleep tips, risk alerts, lifestyle optimization
- **Admin Panel** — Platform metrics, cluster distribution, data quality stats

## Quick Start (Docker)

```bash
# Clone and configure
cp .env.example .env

# Start all services
docker compose up --build

# Access the app
# Frontend: http://localhost:3000
# API Docs:  http://localhost:8000/docs
# Database:  localhost:5432
```

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.12+
- PostgreSQL 16

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

# Start PostgreSQL (or use Docker for DB only)
docker compose up postgres -d

# Run API
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Seed Admin User

```bash
cd backend
python scripts/seed_admin.py
# Creates: admin@sleepanalytics.com / admin123456
```

## Sample Data

Upload the included sample Fitbit CSV to test the pipeline:

```
sample-data/fitbit_sleep_sample.csv
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register new user |
| POST | `/api/auth/login` | Login & get JWT |
| GET | `/api/auth/me` | Current user profile |
| POST | `/api/upload/` | Upload wearable data |
| GET | `/api/upload/history` | Upload history |
| GET | `/api/analytics/summary` | Sleep summary stats |
| POST | `/api/analytics/cluster` | Run clustering analysis |
| GET | `/api/analytics/lifestyle` | Lifestyle correlation analysis |
| POST | `/api/analytics/predict` | Predict sleep archetype |
| GET | `/api/analytics/recommendations` | Get recommendations |
| GET | `/api/analytics/admin/stats` | Admin dashboard stats |

## Database Schema

- **users** — Authentication & roles
- **sleep_records** — Nightly sleep metrics
- **activity_records** — Steps, calories, heart rate
- **health_metrics** — HRV, SpO2, stress scores
- **lifestyle_factors** — Caffeine, exercise, screen time
- **cluster_assignments** — ML cluster results
- **predictions** — Model predictions & SHAP values
- **data_uploads** — Upload tracking & quality scores

## Deployment

### Production Environment Variables

```env
SECRET_KEY=<openssl rand -hex 32>
DATABASE_URL=postgresql://user:pass@host:5432/sleep_analytics
CORS_ORIGINS=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Docker Production

```bash
docker compose -f docker-compose.yml up -d --build
```

### Manual Deployment

**Backend (Railway/Render/Fly.io):**
1. Set `DATABASE_URL` and `SECRET_KEY`
2. Deploy with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Frontend (Vercel):**
1. Set `NEXT_PUBLIC_API_URL` to your API URL
2. Deploy with `npm run build`

**Database:** Use managed PostgreSQL (Supabase, Neon, RDS)

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── auth.py              # JWT authentication
│   │   ├── routers/             # API route handlers
│   │   └── services/            # ML & preprocessing
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # UI components
│   │   ├── contexts/            # Auth context
│   │   └── lib/                 # API client & utils
│   ├── package.json
│   └── Dockerfile
├── sample-data/                 # Test CSV files
├── docker-compose.yml
└── README.md
```

## License

MIT
