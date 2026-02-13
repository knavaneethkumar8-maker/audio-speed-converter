from flask import Flask, render_template, request, send_file, jsonify
from pydub import AudioSegment
import os
import uuid
import shutil

app = Flask(__name__)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clear_directory(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed deleting {file_path}: {e}")


def slow_audio(audio, factor):
    new_frame_rate = int(audio.frame_rate / factor)
    return audio._spawn(
        audio.raw_data, overrides={"frame_rate": new_frame_rate}
    ).set_frame_rate(44100)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("audio")
    if not file:
        return jsonify({"error": "No file"}), 400

    # 🔥 DELETE OLD FILES FIRST
    clear_directory(UPLOAD_DIR)
    clear_directory(OUTPUT_DIR)

    uid = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, uid + "_" + file.filename)
    file.save(input_path)

    audio = AudioSegment.from_file(input_path)

    normal_path = os.path.join(OUTPUT_DIR, f"{uid}_normal.wav")
    slow4_path = os.path.join(OUTPUT_DIR, f"{uid}_slow4x.wav")
    slow8_path = os.path.join(OUTPUT_DIR, f"{uid}_slow8x.wav")
    slow16_path = os.path.join(OUTPUT_DIR, f"{uid}_slow16x.wav")

    audio.export(normal_path, format="wav")
    slow_audio(audio, 4).export(slow4_path, format="wav")
    slow_audio(audio, 8).export(slow8_path, format="wav")
    slow_audio(audio, 16).export(slow16_path, format="wav")

    return jsonify({
        "normal": f"/download/{os.path.basename(normal_path)}",
        "slow4": f"/download/{os.path.basename(slow4_path)}",
        "slow8": f"/download/{os.path.basename(slow8_path)}",
        "slow16": f"/download/{os.path.basename(slow16_path)}"
    })


@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(OUTPUT_DIR, filename), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
