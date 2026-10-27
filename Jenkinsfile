/*
 * Jenkinsfile — Declarative Pipeline for the Iris Prediction Service
 *
 * Stages:
 *   1. Checkout          — pull latest code from GitHub
 *   2. Install Deps      — pip install all requirements
 *   3. Lint              — flake8 code-quality check
 *   4. Unit Tests        — pytest with XML report
 *   5. Train Model       — regenerate model.pkl
 *   6. Build Image       — docker build the production image
 *   7. Deploy            — docker compose up -d
 *   8. Smoke Test        — curl /health to verify deployment
 *   Post section         — always-run success/failure notification
 *
 * Prerequisites on the Jenkins host:
 *   - Python 3.10+ in PATH
 *   - Docker in PATH (Docker socket mounted if running Jenkins in Docker)
 *   - docker-compose / docker compose available
 */

pipeline {

    // Run on any available agent (adjust label to match your Jenkins node)
    agent any

    // ── Environment variables ────────────────────────────────────────────────
    environment {
        IMAGE_NAME   = "iris-predictor"
        IMAGE_TAG    = "latest"
        APP_PORT     = "5000"
        COMPOSE_FILE = "docker-compose.yml"
    }

    // ── Options ──────────────────────────────────────────────────────────────
    options {
        // Fail the build if no activity for 30 minutes
        timeout(time: 30, unit: 'MINUTES')
        // Keep only the last 10 build logs to save disk space
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // Do not allow concurrent builds on the same branch
        disableConcurrentBuilds()
        // Add timestamps to all log lines
        timestamps()
    }

    // ── Triggers ─────────────────────────────────────────────────────────────
    triggers {
        // Poll GitHub every 5 minutes (replace with webhook when possible)
        pollSCM('H/5 * * * *')
    }

    stages {

        // ── Stage 1: Checkout ─────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "╔══════════════════════════════════════╗"
                echo "║  Stage 1: Checkout source code        ║"
                echo "╚══════════════════════════════════════╝"
                // Jenkins checks out the repo automatically via SCM config.
                // This step just prints what was checked out.
                sh '''
                    echo "Branch  : $(git rev-parse --abbrev-ref HEAD)"
                    echo "Commit  : $(git rev-parse --short HEAD)"
                    echo "Author  : $(git log -1 --format="%an <%ae>")"
                    echo "Message : $(git log -1 --format="%s")"
                    ls -la
                '''
            }
        }

        // ── Stage 2: Install Dependencies ────────────────────────────────────
        stage('Install Dependencies') {
            steps {
                echo "╔══════════════════════════════════════╗"
                echo "║  Stage 2: Install Python dependencies ║"
                echo "╚══════════════════════════════════════╝"
                sh '''
                    python3 -m pip install --upgrade pip
                    pip3 install -r requirements.txt
                    echo "Installed packages:"
                    pip3 list
                '''
            }
        }

        // ── Stage 3: Lint ────────────────────────────────────────────────────
        stage('Lint') {
            steps {
                echo "╔══════════════════════════════════════╗"
                echo "║  Stage 3: Code quality check (flake8) ║"
                echo "╚══════════════════════════════════════╝"
                sh '''
                    # Max line length 100 for this project.
                    # W503 is ignored (line break before binary operator - style preference).
                    flake8 app/ train.py tests/ \
                        --max-line-length=100 \
                        --ignore=W503 \
                        --statistics \
                        --count
                '''
            }
        }

        // ── Stage 4: Unit Tests ───────────────────────────────────────────────
        stage('Unit Tests') {
            steps {
                echo "╔══════════════════════════════════════╗"
                echo "║  Stage 4: Run pytest unit tests       ║"
                echo "╚══════════════════════════════════════╝"
                sh '''
                    # Train model first so tests can load model.pkl
                    python3 train.py

                    # Run tests; generate JUnit XML for Jenkins test results
                    pytest tests/ -v \
                        --tb=short \
                        --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    // Publish JUnit test results in Jenkins UI
                    junit 'test-results.xml'
                }
            }
        }

        // ── Stage 5: Train Model ──────────────────────────────────────────────
        stage('Train Model') {
            steps {
                echo "╔══════════════════════════════════════╗"
                echo "║  Stage 5: Train and save model.pkl    ║"
                echo "╚══════════════════════════════════════╝"
                sh '''
                    python3 train.py
                    ls -lh model.pkl
                    echo "Model trained successfully."
                '''
            }
        }

        // ── Stage 6: Build Docker Image ───────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                echo "╔══════════════════════════════════════╗"
                echo "║  Stage 6: Build production Docker image ║"
                echo "╚══════════════════════════════════════╝"
                sh '''
                    docker build \
                        --tag ${IMAGE_NAME}:${IMAGE_TAG} \
                        --tag ${IMAGE_NAME}:build-${BUILD_NUMBER} \
                        --file Dockerfile \
                        .

                    echo "Built image:"
                    docker images | grep ${IMAGE_NAME}
                '''
            }
        }

        // ── Stage 7: Deploy ───────────────────────────────────────────────────
        stage('Deploy') {
            steps {
                echo "╔══════════════════════════════════════╗"
                echo "║  Stage 7: Deploy with Docker Compose  ║"
                echo "╚══════════════════════════════════════╝"
                sh '''
                    # Bring up (or update) the iris-app service only.
                    # Jenkins and monitoring services may already be running.
                    docker compose -f ${COMPOSE_FILE} up -d iris-app

                    echo "Running containers:"
                    docker ps --filter "name=iris-app"
                '''
            }
        }

        // ── Stage 8: Smoke Test ───────────────────────────────────────────────
        stage('Smoke Test') {
            steps {
                echo "╔══════════════════════════════════════╗"
                echo "║  Stage 8: Smoke test /health endpoint  ║"
                echo "╚══════════════════════════════════════╝"
                sh '''
                    # Wait up to 30 s for the container to be healthy
                    MAX_WAIT=30
                    ELAPSED=0
                    until curl -sf http://localhost:${APP_PORT}/health; do
                        sleep 2
                        ELAPSED=$((ELAPSED+2))
                        if [ $ELAPSED -ge $MAX_WAIT ]; then
                            echo "ERROR: App did not become healthy in ${MAX_WAIT}s"
                            exit 1
                        fi
                        echo "  Waiting … ${ELAPSED}s elapsed"
                    done
                    echo ""
                    echo "Smoke test PASSED — /health returned OK"
                '''
            }
        }

    } // end stages

    // ── Post actions ─────────────────────────────────────────────────────────
    post {
        success {
            echo """
╔══════════════════════════════════════════════╗
║  ✅  PIPELINE PASSED                          ║
║  Branch  : ${env.GIT_BRANCH}                 ║
║  Build # : ${env.BUILD_NUMBER}               ║
║  App     : http://localhost:${APP_PORT}      ║
║  Jenkins : ${env.BUILD_URL}                  ║
╚══════════════════════════════════════════════╝
"""
        }
        failure {
            echo """
╔══════════════════════════════════════════════╗
║  ❌  PIPELINE FAILED                          ║
║  Branch  : ${env.GIT_BRANCH}                 ║
║  Build # : ${env.BUILD_NUMBER}               ║
║  Logs    : ${env.BUILD_URL}console           ║
╚══════════════════════════════════════════════╝
"""
        }
        always {
            // Clean up stale test XML if present from a previous failed build
            cleanWs(patterns: [[pattern: 'test-results.xml', type: 'INCLUDE']])
        }
    }
}
