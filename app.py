from flask import Flask, render_template, send_from_directory

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/static/<path:path>")
def send_report(path):
    return send_from_directory("static", path)
