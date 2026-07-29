# FinLens — Project Brief

## Overview

FinLens is a personal fintech portfolio project that aggregates data from multiple mock financial accounts into a single unified view, surfaces proactive spending insights, and runs a background fraud/anomaly check on transaction activity.

The project is built to demonstrate three real, current fintech engineering themes in one coherent system: open banking-style data aggregation, AI-adjacent insight generation, and fraud detection — rather than three disconnected demos.

## Current status

- **Aggregation service:** Spring Boot 3.4.1 (Java 17, Maven)
- **Insights service:** FastAPI (Python 3.12)
- **Fraud service:** FastAPI (Python 3.12)
- **Frontend:** React 19 + Vite + TypeScript
- **Database:** PostgreSQL
- **Containerization:** Docker + Docker Compose
- **CI/CD:** GitHub Actions — build, test, and Docker image build on push to `main`

## Services

| Service | Language | Framework | Port |
|---|---|---|---|
| `aggregation-service` | Java 17 | Spring Boot 3.4.1 | 8080 |
| `insights-service` | Python 3.12 | FastAPI | 8000 |
| `fraud-service` | Python 3.12 | FastAPI | 8001 |
| `frontend` | TypeScript | React 19 / Vite | 5173 |

## Why this project

Current fintech industry trends point to three specific gaps this project addresses directly:

- **Aggregation:** Open banking and API-first infrastructure are a core 2026 fintech theme — fintechs are increasingly built as modular platforms that unify data across sources rather than siloed apps.
- **Insight generation:** Consumer research shows most fintech app users want proactive financial guidance, not just raw data — and most apps currently fail to deliver this.
- **Fraud detection:** Fraud is becoming more sophisticated industry-wide, making anomaly detection a standard, expected layer in any transaction-handling system.

## Core features (v1 scope)

1. **Account aggregation**
   - 2-3 mock account types (e.g. checking, savings, credit card), each with seeded synthetic transaction data
   - Single unified API response normalizing all account types into one schema
   - JWT-based authentication with register and login endpoints

2. **Proactive insights**
   - Rule-based observations generated from aggregated data, e.g.:
     - **Spending increase by category** — compares current month total to prior 2-month average, flags categories with ≥25% increase
     - **Recurring subscription detection** — groups transactions by description and amount, identifies monthly charges with 25–35 day gaps
     - **Balance trend projection** — projects days until zero based on average daily net change over the last 14 days

3. **Fraud/anomaly check**
   - Runs as a background check on incoming transactions
   - **Velocity check** — detects bursts of outgoing transactions exceeding a threshold within a rolling time window (e.g. 5 transactions in 10 minutes)

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │     │  Insights    │     │    Fraud     │
│   React 19   │     │  FastAPI     │     │  FastAPI     │
│   :5173      │     │  :8000       │     │  :8001       │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └─────────┬──────────┴──────────┬─────────┘
                 │                     │
        ┌────────▼────────┐   ┌───────▼────────┐
        │  Aggregation    │   │  PostgreSQL    │
        │  Spring Boot    │   │  :5432         │
        │  :8080          │   └────────────────┘
        └─────────────────┘
```

## Running locally

### Prerequisites
- Java 17, Maven, Python 3.12, Node.js 20+
- Docker (optional, for Postgres)

### 1. Start PostgreSQL
```bash
docker compose up -d postgres
```

### 2. Start the aggregation service
```bash
cd aggregation-service
mvn spring-boot:run
```

### 3. Start the insights service
```bash
cd insights-service
python -m venv venv && .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Start the fraud service
```bash
cd fraud-service
python -m venv venv && .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### 5. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend dev server proxies `/api/*` requests to the aggregation service at `localhost:8080`.

### Docker Compose (everything)
```bash
docker compose up --build
```

### Running tests

```bash
# Aggregation service
cd aggregation-service && mvn clean test

# Insights service
cd insights-service && .\venv\Scripts\python -m pytest tests/ -v

# Fraud service
cd fraud-service && .\venv\Scripts\python -m pytest tests/ -v
```

## API overview

### Aggregation service (`:8080`)

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/accounts` | List accounts with transactions (requires JWT) |

### Insights service (`:8000`)

| Method | Path | Description |
|---|---|---|
| GET | `/insights/{user_id}` | Spending alerts, subscriptions, balance projection |
| GET | `/health` | Health check |

### Fraud service (`:8001`)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |

## Frontend

The React frontend provides:

- **Login page** — email/password form that calls `/api/auth/login`, stores the JWT in localStorage, and redirects to the dashboard
- **Dashboard** — protected route that requires a valid JWT; displays the authenticated user's email and a sign-out button (account data and insights to follow)

## Project structure

```
finlens/
├── aggregation-service/    # Spring Boot — account data & auth
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/
├── insights-service/       # FastAPI — spending insights
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── insights.py     # Core insight functions
│       ├── main.py
│       └── models.py
├── fraud-service/          # FastAPI — fraud detection
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── fraud.py        # Velocity check
│       └── main.py
├── frontend/               # React 19 + Vite
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── auth/           # AuthContext, ProtectedRoute
│       └── pages/          # LoginPage, DashboardPage
├── docker-compose.yml
├── .github/workflows/ci.yml
└── README.md
```

## Explicitly out of scope for v1

- Real bank/payment integration of any kind
- Kubernetes or multi-region deployment
- Mobile app
- Complex multi-user roles or permissions beyond basic auth

## Cost estimate

Estimated **€0/month** for the first 12 months using AWS free tier (EC2 + RDS), with a billing alert set at $5 as a safeguard. After the free tier period, estimated **€10-15/month** if kept running continuously — recommend stopping/terminating resources once the project has served its demonstration purpose.

## Success criteria

- Live, publicly accessible deployment with a real URL
- Clean, documented GitHub repository pinned under the primary account
- At least one blog post derived from the build (technical deep-dive, cloud/infra decisions, or the insight/fraud logic)
- Demonstrable in an interview: can explain the aggregation schema, the insight rules, and the anomaly detection approach without notes