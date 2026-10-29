# 🌸 Iris Species Prediction Service — MLOps CI/CD Demo

> **Course:** ML DevOps Laboratory (UDSPC0732) — ISE-2  
> **Student:** Raviraj Amol Patil | Semester VII | CSE (Data Science)

---

## Problem Statement

Build an automated CI/CD pipeline for an Iris species classification microservice that demonstrates:
- Continuous Integration (automated testing, linting, model training)
- Continuous Deployment (Docker image build + Compose-based deploy)
- Real-time monitoring with Prometheus and Grafana

---

## Architecture

```
GitHub → Jenkins → Docker Build → Deploy → Prometheus → Grafana
                        ↓
                   Iris Flask App (/predict, /health, /metrics)
```

---

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| ML | scikit-learn, joblib | RandomForest on Iris dataset |
| API | Flask + Gunicorn | REST API + HTML UI |
| Tests | pytest, flake8 | Unit tests + linting |
| VCS | Git + GitHub | Source control |
| CI/CD | Jenkins | Pipeline automation |
| Containers | Docker + Compose | Packaging & orchestration |
| Monitoring | Prometheus + Grafana | Metrics & dashboards |

---

## Quick Start (Local, without Docker)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train the model
python train.py

# 3. Start the Flask app
python -m app.app

# 4. Test endpoints
curl http://localhost:5000/health
curl -X POST http://localhost:5000/predict \
     -H "Content-Type: application/json" \
     -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'

# 5. Run tests
pytest tests/ -v

# 6. Lint check
flake8 app/ train.py tests/ --max-line-length=100
```

---

## Docker Quick Start

```bash
# Build the image
docker build -t iris-predictor:latest .

# Run the container
docker run -d -p 5000:5000 --name iris-app iris-predictor:latest

# Test it
curl http://localhost:5000/health

# Full stack (app + Jenkins + Prometheus + Grafana)
docker compose up -d
```

**Service URLs:**

| Service | URL | Credentials |
|---------|-----|-------------|
| Iris App | http://localhost:5000 | — |
| Jenkins | http://localhost:8085 | admin / (see initial password) |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin123 |

---

## API Reference

### `GET /health`
Returns `{"status": "ok", "service": "iris-predictor"}` with HTTP 200.

### `POST /predict`
**Body:**
```json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
```
**Response:**
```json
{
  "class_name": "setosa",
  "class_index": 0,
  "features": [5.1, 3.5, 1.4, 0.2]
}
```

### `GET /metrics`
Prometheus-format metrics.

---

## CI/CD Pipeline (Jenkins Stages)

| Stage | What it does |
|-------|-------------|
| Checkout | Pull latest code from GitHub |
| Install Deps | `pip install -r requirements.txt` |
| Lint | `flake8` code quality check |
| Unit Tests | `pytest tests/` + publish JUnit XML |
| Train Model | `python train.py` → model.pkl |
| Build Image | `docker build` |
| Deploy | `docker compose up -d iris-app` |
| Smoke Test | `curl /health` to verify deployment |

---

## Generate Traffic (for Grafana graphs)

```bash
python traffic/generate_traffic.py --n 200 --url http://localhost:5000
```

---

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── app.py          # Flask routes + Prometheus metrics
│   └── model.py        # Model loader + predict()
├── tests/
│   └── test_app.py     # pytest tests
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/provisioning/
│       ├── datasources/prometheus.yml
│       └── dashboards/
│           ├── dashboard.yml
│           └── iris_dashboard.json
├── traffic/
│   └── generate_traffic.py
├── docs/screenshots/   # evidence screenshots
├── train.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── Jenkinsfile
└── README.md
```

---

## GitHub Repository

`https://github.com/<your-username>/ml-cicd-monitoring-demo`

---

## Course Outcomes

- **CO1 (L2 — Understand):** Understand and explain CI/CD pipeline concepts, containerization, and monitoring.
- **CO4 (L4 — Analyze):** Analyze and evaluate pipeline failures, monitoring data, and system health metrics.
# ISE_2_MLDEVOPS_
