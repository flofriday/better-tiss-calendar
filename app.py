from flask import Flask, render_template, send_from_directory, abort, request

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/static/<path:path>")
def send_report(path):
    return send_from_directory("static", path)


@app.route("/verify")
def verify():
    url = request.args.get("url")
    if url is None:
        return "No url provided", 400
    return "Ok"


@app.route("/tiss.ical")
def icalendar():
    abort(501)
