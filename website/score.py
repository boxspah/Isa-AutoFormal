import base64
import glob
import json
import os
import subprocess
import threading

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from pyngrok import ngrok

port = 4040

app = Flask(__name__, template_folder=".")
app.secret_key = "your secret key"
CORS(app)


def select_data(train_number, test_number):
    if train_number:
        data_path = os.path.join(
            "../dataset/MATH/batch/task_train_gpt-4", str(train_number)
        )
    elif test_number:
        data_path = os.path.join(
            "../dataset/MATH/batch/task_test_gpt-4", str(test_number)
        )
    tmp_path = os.path.join("./tmp", data_path)
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    print(data_path)
    files = glob.glob(os.path.join(data_path, "**", "*.json"), recursive=True)
    session["idx"] = -1
    session["files"] = files
    session["path"] = tmp_path


@app.route("/", methods=["GET", "POST"])
def select_number():
    if request.method == "POST":
        train_number = request.form.get("train")
        test_number = request.form.get("test")
        select_data(train_number, test_number)
        return redirect(url_for("index"))
    return render_template("main.html")


@app.route("/")
def home():
    return render_template("main.html")


@app.route("/index", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/data", methods=["GET", "POST"])
def data():
    files = session["files"]
    idx = session["idx"]
    if request.method == "POST":
        data = request.get_json()
        print(data)
        with open(files[idx], "w") as f:
            json.dump(data, f, indent=4)
        return jsonify({"status": "success"})
    else:
        j = 0
        while idx == -1:
            with open(files[j]) as f:
                data = json.load(f)
            for i in range(10):
                tmp = "a_%s" % (i)
                if "label" not in data[tmp]:
                    idx = j
            j += 1
        with open(files[idx]) as f:
            data = json.load(f)
        if "prediction" in data:
            components = [data["prediction"][key] for key in data["prediction"].keys()]
        else:
            components = "None"
        data["str_pred"] = str(components)
        session["idx"] = idx
        return jsonify({"data": data, "idx": idx})


@app.route("/previous", methods=["GET"])
def previous():
    files = session["files"]
    session["idx"] = max(0, session["idx"] - 1)
    with open(files[session["idx"]]) as f:
        data = json.load(f)
    return jsonify(data)


@app.route("/next", methods=["GET"])
def next():
    files = session["files"]
    session["idx"] = min(len(files) - 1, session["idx"] + 1)
    with open(files[session["idx"]]) as f:
        data = json.load(f)
    return jsonify(data)


@app.route("/jump/<int:jumpIndex>", methods=["GET"])
def jump(jumpIndex):
    files = session["files"]
    session["idx"] = min(len(files) - 1, jumpIndex)
    with open(files[session["idx"]]) as f:
        data = json.load(f)
    return jsonify(data)


@app.route("/asy_endpoint", methods=["POST"])
def handle_asy():
    tmp_path = session["tmp_path"]
    asy_code = "size(16cm, 8cm);\n" + request.json["asy_code"]
    with open(tmp_path + "/output_%s.asy" % (session["idx"]), "w") as temp:
        temp.write(asy_code)
    try:
        result = subprocess.check_output(
            [
                "asy",
                "-noView",
                "-f",
                "png",
                "-o",
                tmp_path + "/output_%s.asy" % (session["idx"]),
                tmp_path + "/output_%s.asy" % (session["idx"]),
            ]
        )
    except Exception as e:
        print("asy error: %s" % (e))
    try:
        with open(tmp_path + "/output_%s.png" % (session["idx"]), "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print("image error: %s" % (e))
    return jsonify({"image": encoded_string})


def run(port):
    app.run(port=port)


if __name__ == "__main__":
    # Run the Flask app in a new thread
    threading.Thread(target=run, args=(port,)).start()

    # Open a ngrok tunnel to the flask app
    public_url = ngrok.connect(port)
    print("Public URL:", public_url)
