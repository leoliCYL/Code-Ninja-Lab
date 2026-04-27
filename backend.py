import cv2
import time
import json
from flask import Flask, render_template, Response
from main import PasswordApp
from dotenv import load_dotenv

app = Flask(__name__)
password_app = None


def frame_generator(camera):
    while True:
        frame = camera.get_frame()
        if frame is None:
            time.sleep(1/30)
            continue
        frame = cv2.resize(frame, (640, 480))
        ret, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
        time.sleep(1/30)


@app.route('/video_feed')
def video_feed():
    return Response(frame_generator(password_app), mimetype='multipart/x-mixed-replace; boundary=frame')


def event_generator():
    # Send current state immediately so the browser is in sync on connect/reconnect
    yield f'data: {json.dumps({"state": password_app.app_state, "gameId": password_app.current_gameId})}\n\n'
    while True:
        state = password_app.event_queue.get()
        yield f'data: {json.dumps(state)}\n\n'
        password_app.event_queue.task_done()


@app.route('/event_stream')
def event_stream():
    return Response(event_generator(), mimetype='text/event-stream')


@app.route('/')
def home_page():
    return render_template('index.html')


if __name__ == '__main__':
    load_dotenv()
    password_app = PasswordApp()
    app.run(host='127.0.0.1', port=5000, threaded=True, use_reloader=False)
