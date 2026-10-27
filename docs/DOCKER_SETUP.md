# Docker Setup Guide for ISE-2 MLOps Lab

## Check 1: Is Docker Desktop installed?

Open PowerShell and run:
```powershell
docker --version
```

If you get "not recognized", follow the steps below.

---

## Step 1: Install WSL 2 (Run as Administrator)

```powershell
# Open PowerShell as Administrator, then:
wsl --install
```
**Restart your PC after this step.**

---

## Step 2: Install Docker Desktop

After restarting, open PowerShell and run:
```powershell
winget install Docker.DockerDesktop
```

OR download from: https://www.docker.com/products/docker-desktop/

**Important installation settings:**
- ✅ Use WSL 2 based engine (recommended)
- ✅ Add Docker Desktop to PATH

---

## Step 3: Start Docker Desktop

1. Search for "Docker Desktop" in Start Menu and open it
2. Wait until the bottom-left shows a **green "Engine running"** status
3. Accept the terms if prompted

---

## Step 4: Verify in a NEW PowerShell window

```powershell
docker --version
# Expected: Docker version XX.X.X

docker compose version  
# Expected: Docker Compose version v2.XX.X

docker run hello-world
# Expected: "Hello from Docker!" message
```

---

## Step 5: Run the Full Stack

Once Docker is working, run from the project directory:

```powershell
cd "C:\ISE 2 MLDEVOPS"

# Build and start everything
docker compose up -d

# Check all services are running
docker ps

# Service URLs:
# http://localhost:5000  → Iris Predictor App
# http://localhost:8080  → Jenkins CI/CD
# http://localhost:9090  → Prometheus
# http://localhost:3000  → Grafana (admin / admin123)
```

---

## Jenkins First-Time Setup

After `docker compose up -d`:

1. Go to http://localhost:8080
2. Get the initial password:
   ```powershell
   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```
3. Paste the password in the Jenkins setup wizard
4. Click "Install suggested plugins"
5. Also install these additional plugins:
   - **Git Plugin**
   - **Pipeline**
   - **Docker Pipeline**
   - **GitHub Integration**

6. Create your admin user

7. Create a new Pipeline job:
   - New Item → "iris-predictor-pipeline" → Pipeline
   - Definition: Pipeline script from SCM
   - SCM: Git
   - Repository URL: https://github.com/ravipatil-9225/ISE2_MLDEVOPS.git
   - Branch: */main
   - Script Path: Jenkinsfile
   - Build Triggers: Poll SCM → `H/5 * * * *`

8. Click "Build Now" to trigger the first pipeline run

---

## Prometheus Targets Verification

Go to: http://localhost:9090/targets

You should see:
- `iris-predictor` — State: UP ✅
- `prometheus` — State: UP ✅

---

## Grafana Dashboard

1. Go to http://localhost:3000
2. Login: admin / admin123
3. Go to Dashboards → MLOps Lab → "Iris Predictor — MLOps Dashboard"

The dashboard loads automatically via provisioning (no manual setup needed).

Generate traffic to see graphs:
```powershell
python traffic/generate_traffic.py --n 200 --url http://localhost:5000
```
