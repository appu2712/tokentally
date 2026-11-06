"""
Zero-dependency interactive local web dashboard for TokenTally.
Provides real-time token counting, pricing simulation, and visual model comparisons.
"""

import http.server
import json
import socketserver
import urllib.parse
from typing import Any, Dict

from .counter import count_tokens
from .calculator import estimate_cost, compare_models
from .models import MODEL_REGISTRY, list_supported_models
from .optimizer import optimize_prompt

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TokenTally — LLM Token & Cost Studio</title>
  <style>
    :root {
      --bg: #0b0f17;
      --card: #131b26;
      --border: #233144;
      --text: #f0f4fc;
      --text-dim: #8b9bb4;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.15);
      --green: #34d399;
      --purple: #a855f7;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
    .container { max-width: 1200px; margin: 0 auto; }
    header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
    .logo { font-size: 22px; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 8px; }
    .badge { background: var(--accent-glow); color: var(--accent); border: 1px solid var(--accent); padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
    .card h2 { font-size: 16px; font-weight: 600; margin-bottom: 16px; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; }
    textarea { width: 100%; height: 260px; background: #070a0f; border: 1px solid var(--border); border-radius: 8px; color: var(--text); padding: 14px; font-family: monospace; font-size: 14px; resize: vertical; outline: none; }
    textarea:focus { border-color: var(--accent); }
    .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; }
    label { font-size: 12px; color: var(--text-dim); margin-bottom: 6px; display: block; }
    select, input[type="number"], input[type="range"] { width: 100%; background: #070a0f; border: 1px solid var(--border); border-radius: 6px; color: var(--text); padding: 8px 12px; outline: none; }
    .stat-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 18px; }
    .stat-box { background: #090e16; border: 1px solid var(--border); padding: 14px; border-radius: 8px; }
    .stat-label { font-size: 12px; color: var(--text-dim); }
    .stat-value { font-size: 24px; font-weight: 700; color: var(--accent); margin-top: 4px; }
    .stat-cost { color: var(--green); }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13px; }
    th { text-align: left; color: var(--text-dim); padding: 8px; border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
    td { padding: 10px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .bar-bg { width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; margin-top: 4px; }
    .bar-fill { height: 100%; background: var(--accent); border-radius: 3px; }
    .btn { background: var(--accent); color: #000; border: none; font-weight: 600; padding: 10px 18px; border-radius: 6px; cursor: pointer; transition: 0.2s; }
    .btn:hover { opacity: 0.9; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo">⚡ TokenTally <span>Studio</span></div>
      <div class="badge">v0.1.0 • Live Dashboard</div>
    </header>

    <div class="grid">
      <!-- Input Panel -->
      <div class="card">
        <h2>Input Prompt & Scenario</h2>
        <textarea id="promptInput" placeholder="Paste your prompt, codebase excerpt, or system instructions here..."></textarea>

        <div class="controls">
          <div>
            <label>Selected Model</label>
            <select id="modelSelect"></select>
          </div>
          <div>
            <label>Estimated Completion Tokens (<span id="compVal">500</span>)</label>
            <input type="range" id="compRange" min="0" max="4000" step="50" value="500">
          </div>
        </div>
      </div>

      <!-- Live Analysis Panel -->
      <div class="card">
        <h2>Live Cost & Token Metrics</h2>
        <div class="stat-cards">
          <div class="stat-box">
            <div class="stat-label">Prompt Tokens</div>
            <div class="stat-value" id="tokenCount">0</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Estimated Dollar Cost</div>
            <div class="stat-value stat-cost" id="totalCost">$0.000000</div>
          </div>
        </div>

        <h2>Multi-Model Cost Comparison</h2>
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Provider</th>
              <th>Est. Cost</th>
              <th>Ratio</th>
            </tr>
          </thead>
          <tbody id="comparisonBody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    const promptInput = document.getElementById('promptInput');
    const modelSelect = document.getElementById('modelSelect');
    const compRange = document.getElementById('compRange');
    const compVal = document.getElementById('compVal');
    const tokenCount = document.getElementById('tokenCount');
    const totalCost = document.getElementById('totalCost');
    const compBody = document.getElementById('comparisonBody');

    // Populate models
    fetch('/api/models')
      .then(res => res.json())
      .then(models => {
        models.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m;
          opt.textContent = m;
          if (m === 'gpt-4o') opt.selected = true;
          modelSelect.appendChild(opt);
        });
      });

    compRange.addEventListener('input', () => {
      compVal.textContent = compRange.value;
      updateMetrics();
    });

    promptInput.addEventListener('input', updateMetrics);
    modelSelect.addEventListener('change', updateMetrics);

    function updateMetrics() {
      const text = promptInput.value || ' ';
      const model = modelSelect.value || 'gpt-4o';
      const comp = parseInt(compRange.value) || 0;

      fetch('/api/calculate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: text, model: model, completion_tokens: comp})
      })
      .then(res => res.json())
      .then(data => {
        tokenCount.textContent = data.input_tokens.toLocaleString();
        totalCost.textContent = '$' + data.total_cost_usd.toFixed(6);
      });

      fetch('/api/compare', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: text})
      })
      .then(res => res.json())
      .then(rows => {
        compBody.innerHTML = '';
        rows.forEach(r => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><strong>${r.model}</strong></td>
            <td><span style="color:var(--text-dim)">${r.provider}</span></td>
            <td style="color:var(--green)">$${r.total_cost_usd.toFixed(6)}</td>
            <td><code>${r.relative_ratio.toFixed(2)}x</code></td>
          `;
          compBody.appendChild(tr);
        });
      });
    }

    // Default sample prompt
    promptInput.value = "You are an expert distributed systems engineer. Explain the raft consensus algorithm with state diagrams, leader election criteria, and log compaction strategies in high detail.";
    setTimeout(updateMetrics, 200);
  </script>
</body>
</html>
"""


class DashboardRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler for TokenTally local studio web dashboard."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
        elif parsed.path == "/api/models":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            models = list_supported_models()
            self.wfile.write(json.dumps(models).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if parsed.path == "/api/calculate":
            prompt = payload.get("prompt", "")
            model = payload.get("model", "gpt-4o")
            comp = payload.get("completion_tokens", 0)
            res = estimate_cost(prompt, model=model, completion_tokens=comp)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res.to_dict()).encode("utf-8"))

        elif parsed.path == "/api/compare":
            prompt = payload.get("prompt", "")
            rows = compare_models(prompt)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps([r.to_dict() for r in rows]).encode("utf-8"))

        else:
            self.send_error(404, "Endpoint not found")

    def log_message(self, format, *args):
        # Silence default HTTP server logging for clean terminal experience
        pass


def start_server(port: int = 7860, host: str = "127.0.0.1") -> None:
    """Start the interactive local web dashboard."""
    server_address = (host, port)
    with socketserver.TCPServer(server_address, DashboardRequestHandler) as httpd:
        print(f"\n⚡ TokenTally Studio running at http://{host}:{port}/")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
