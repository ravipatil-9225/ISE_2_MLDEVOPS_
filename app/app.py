"""
app/app.py - Flask application for the Iris Species Prediction Service.

Endpoints:
    GET  /          - Web UI with an HTML form for browser-based predictions
    GET  /health    - Liveness/readiness probe (used by Jenkins smoke test)
    POST /predict   - JSON API for ML inference
    GET  /metrics   - Prometheus metrics (scraped by Prometheus server)
"""

import os
import time
import logging

from flask import Flask, request, jsonify, render_template_string
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter

from app.model import load_model, predict as model_predict

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Flask app ──────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── Prometheus metrics ─────────────────────────────────────────────────────────
# PrometheusMetrics automatically tracks:
#   - http_request_duration_seconds (histogram → gives p50/p95/p99)
#   - http_requests_total           (counter, labelled by method/path/status)
metrics = PrometheusMetrics(app)

# Custom counter: how many predictions per Iris class have been served
PREDICTION_COUNTER = Counter(
    "iris_predictions_total",
    "Total number of Iris species predictions",
    ["class_name"],   # label dimension
)

# Custom counter: total prediction errors
ERROR_COUNTER = Counter(
    "iris_prediction_errors_total",
    "Total number of prediction errors (bad input, model error, etc.)",
)

# ── HTML template (served on GET /) ───────────────────────────────────────────
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Iris Species Predictor</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      min-height: 100vh;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      display: flex; align-items: center; justify-content: center;
      padding: 20px;
    }
    .card {
      background: rgba(255,255,255,0.08);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 20px;
      padding: 40px;
      width: 100%; max-width: 520px;
      box-shadow: 0 25px 50px rgba(0,0,0,0.4);
    }
    h1 {
      color: #e94560;
      font-size: 1.8rem;
      margin-bottom: 6px;
      text-align: center;
    }
    .subtitle {
      color: rgba(255,255,255,0.55);
      text-align: center;
      font-size: 0.9rem;
      margin-bottom: 30px;
    }
    label {
      display: block;
      color: rgba(255,255,255,0.8);
      font-size: 0.85rem;
      margin-bottom: 6px;
      margin-top: 16px;
    }
    input[type=number] {
      width: 100%;
      padding: 10px 14px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.2);
      background: rgba(255,255,255,0.07);
      color: #fff;
      font-size: 1rem;
      transition: border-color 0.2s;
    }
    input[type=number]:focus {
      outline: none;
      border-color: #e94560;
    }
    button {
      margin-top: 24px;
      width: 100%;
      padding: 13px;
      background: linear-gradient(90deg, #e94560, #c0392b);
      color: #fff;
      border: none;
      border-radius: 10px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.15s, box-shadow 0.15s;
    }
    button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(233,69,96,0.4); }
    #result {
      margin-top: 22px;
      padding: 16px;
      border-radius: 12px;
      text-align: center;
      font-size: 1.1rem;
      font-weight: 600;
      display: none;
    }
    .success { background: rgba(46,204,113,0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .error   { background: rgba(231,76,60,0.2);  color: #e74c3c;  border: 1px solid #e74c3c; }
    .links {
      margin-top: 24px;
      display: flex;
      gap: 10px;
      justify-content: center;
    }
    .links a {
      color: rgba(255,255,255,0.5);
      font-size: 0.8rem;
      text-decoration: none;
      padding: 4px 10px;
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 6px;
      transition: color 0.2s;
    }
    .links a:hover { color: #e94560; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🌸 Iris Predictor</h1>
    <p class="subtitle">MLOps Demo — ISE-2 Project by Raviraj Amol Patil</p>

    <form id="predictForm">
      <label>Sepal Length (cm)</label>
      <input id="sl" type="number" step="0.1" value="5.1" required/>
      <label>Sepal Width (cm)</label>
      <input id="sw" type="number" step="0.1" value="3.5" required/>
      <label>Petal Length (cm)</label>
      <input id="pl" type="number" step="0.1" value="1.4" required/>
      <label>Petal Width (cm)</label>
      <input id="pw" type="number" step="0.1" value="0.2" required/>
      <button type="submit">Predict Species</button>
    </form>

    <div id="result"></div>

    <div class="links">
      <a href="/health">Health</a>
      <a href="/metrics">Metrics</a>
    </div>
  </div>

  <script>
    document.getElementById('predictForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const body = {
        sepal_length: parseFloat(document.getElementById('sl').value),
        sepal_width:  parseFloat(document.getElementById('sw').value),
        petal_length: parseFloat(document.getElementById('pl').value),
        petal_width:  parseFloat(document.getElementById('pw').value),
      };
      const div = document.getElementById('result');
      try {
        const res = await fetch('/predict', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(body),
        });
        const data = await res.json();
        if (res.ok) {
          div.className = 'success';
          div.textContent = '🌺 Predicted Species: ' + data.class_name.toUpperCase();
        } else {
          div.className = 'error';
          div.textContent = '⚠ Error: ' + (data.error || 'Unknown error');
        }
      } catch(err) {
        div.className = 'error';
        div.textContent = '⚠ Network error: ' + err.message;
      }
      div.style.display = 'block';
    });
  </script>
</body>
</html>
"""

# ── Routes ─────────────────────────────────────────────────────────────────────


@app.route("/", methods=["GET"])
def index():
    """Serve the HTML prediction form."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/health", methods=["GET"])
@metrics.do_not_track()  # don't pollute metrics with health-check noise
def health():
    """
    Health-check endpoint.
    Returns HTTP 200 when the app is up and the model is loaded.
    Jenkins smoke test hits this after each deploy.
    """
    return jsonify({"status": "ok", "service": "iris-predictor"}), 200


@app.route("/predict", methods=["POST"])
def predict():
    """
    JSON API endpoint for Iris species prediction.

    Expected request body:
        {
            "sepal_length": float,
            "sepal_width":  float,
            "petal_length": float,
            "petal_width":  float
        }

    Returns:
        {
            "class_name":  str,
            "class_index": int,
            "features":    [float, float, float, float]
        }
    """
    start = time.time()

    # ── Validate content type ──────────────────────────────────────────────────
    if not request.is_json:
        ERROR_COUNTER.inc()
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()

    # ── Extract and validate features ─────────────────────────────────────────
    required_fields = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        ERROR_COUNTER.inc()
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        features = [float(data[f]) for f in required_fields]
    except (TypeError, ValueError) as exc:
        ERROR_COUNTER.inc()
        return jsonify({"error": f"Invalid numeric value: {exc}"}), 422

    # ── Inference ──────────────────────────────────────────────────────────────
    try:
        result = model_predict(features)
    except Exception as exc:  # noqa: BLE001
        ERROR_COUNTER.inc()
        logger.exception("Prediction failed")
        return jsonify({"error": str(exc)}), 500

    # ── Record custom metric ───────────────────────────────────────────────────
    PREDICTION_COUNTER.labels(class_name=result["class_name"]).inc()

    duration_ms = (time.time() - start) * 1000
    logger.info(
        "Predicted %s in %.2f ms for features %s",
        result["class_name"], duration_ms, features,
    )

    return jsonify({
        "class_name": result["class_name"],
        "class_index": result["class_index"],
        "features": features,
    }), 200


# ── Entry point (development only) ────────────────────────────────────────────
if __name__ == "__main__":
    # Load model, then start the dev server
    load_model()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
