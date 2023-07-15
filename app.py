from flask import Flask, render_template, send_from_directory, abort, request

import requests
import tiss
from cal_formatter import improve_calendar

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

    # FIXME: Propper url parsing, this could maybe lead to an attack by adding an
    # @ and using it as a username.
    if not url.startswith("https://tiss.tuwien.ac.at/events/rest/calendar/personal"):
        return "The url must point to the TISS calendar", 400

    try:
        tiss.get_calendar(url)
    except requests.exceptions.HTTPError:
        return "TISS rejected this url. Maybe the token is invalid?", 400
    except requests.exceptions.ConnectionError:
        return "Could not contact TISS. Maybe TISS is down?", 400
    except ValueError:
        return "TISS didn't return an ical file, did you paste the correct url?", 400
    except:
        return "Somthing unexpected went wrong, maybe create an GitHub issue?", 500

    return "Ok"


@app.route("/personal.ics")
def icalendar():
    token = request.args.get("token")
    if token is None:
        return "No token provided", 400

    # FIXME: is that required?
    locale = request.args.get("locale")
    if locale is None:
        return "No locale provided", 400

    is_google = "google" in request.args.keys()

    url = f"https://tiss.tuwien.ac.at/events/rest/calendar/personal?token={token}&locale={locale}"
    cal = tiss.get_calendar(url)
    cal = improve_calendar(cal, google_cal=is_google)

    return cal.to_ical(), 200, {"Content-Type": "text/calendar; charset=utf-8"}
