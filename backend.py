# Based on: https://medium.com/@jadomene99/integrating-your-opencv-project-into-a-react-component-using-flask-6bcf909c07f4

import cv2
from flask import Flask, render_template, Response
from main import PasswordApp
import time
import json

# Need to replace with the fram from Leo's OpenCV code in main.py
class VideoCamera:
    def __init__(self):
      self.video = cv2.VideoCapture(0)

    def __del__(self):
      self.video.release()

    def get_frame(self):
      ret, frame = self.video.read()
      return frame

password_app = PasswordApp()

app = Flask(__name__)

def frame_generator(camera):
    while True:
        frame = camera.get_frame()
        frame = cv2.resize(frame, (640, 480))
        ret, jpeg = cv2.imencode('.jpg', frame)
        buffer = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(frame_generator(password_app), mimetype='multipart/x-mixed-replace; boundary=frame')

def event_generator():
    current_state = password_app.app_state
    while True:
        state = password_app.event_queue.get()
        yield f'data: {json.dumps({'state': state})}\n\n'
        password_app.event_queue.task_done()

@app.route('/event_stream')
def event_stream():
    return Response(event_generator(), mimetype='text/event-stream')

@app.route('/')
def home_page():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, threaded=True, use_reloader=False)
