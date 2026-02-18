# Based on: https://medium.com/@jadomene99/integrating-your-opencv-project-into-a-react-component-using-flask-6bcf909c07f4

import cv2
from flask import Flask, render_template, Response
from main import PasswordApp

# Need to replace with the fram from Leo's OpenCV code in main.py
class VideoCamera:
    def __init__(self):
      self.video = cv2.VideoCapture(0)

    def __del__(self):
      self.video.release()

    def get_frame(self):
      ret, frame = self.video.read()
      return frame


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')

def gen(camera):
    while True:
        ret, jpeg = cv2.imencode('.jpg', camera.get_frame())
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(PasswordApp()), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, threaded=True, use_reloader=False)
