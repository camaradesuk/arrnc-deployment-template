from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)
AUDIO_FOLDER = 'audio_data'

@app.route('/')
def index():
    files = [f for f in os.listdir(AUDIO_FOLDER) if os.path.isfile(os.path.join(AUDIO_FOLDER, f))]
    return render_template('index.html', files=files)

@app.route('/audio/<filename>')
def audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
