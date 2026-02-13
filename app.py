from flask import Flask, render_template, request, send_file, jsonify
import os
import uuid
import shutil
import subprocess

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


def sox_slow_audio(input_path, output_path, speed):
    """
    speed < 1.0 → slower
    speed = 0.5 → 2× slower
    """
    cmd = [
        "sox",
        input_path,
        output_path,
        "tempo",
        "-s",
        str(speed)
    ]
    subprocess.run(cmd, check=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("audio")
    speed = request.form.get("speed", type=float)

    if not file:
        return jsonify({"error": "No file"}), 400

    if not speed or speed <= 0 or speed > 1:
        return jsonify({"error": "Invalid speed"}), 400

    clear_directory(UPLOAD_DIR)
    clear_directory(OUTPUT_DIR)

    uid = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, uid + "_" + file.filename)
    file.save(input_path)

    normal_path = os.path.join(OUTPUT_DIR, f"{uid}_normal.wav")
    slow_path = os.path.join(OUTPUT_DIR, f"{uid}_slow_{speed}.wav")

    # Convert original → wav
    subprocess.run(["sox", input_path, normal_path], check=True)

    # Slow using sox tempo
    sox_slow_audio(normal_path, slow_path, speed)

    return jsonify({
        "normal": f"/download/{os.path.basename(normal_path)}",
        "slow": f"/download/{os.path.basename(slow_path)}"
    })


@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(OUTPUT_DIR, filename), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
