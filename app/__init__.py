import json
import sqlite3
from urllib.parse import urlparse

import requests
from flask import Flask, g, render_template, request, send_from_directory

import app.tiss as tiss
from app.format import improve_calendar
from app.monitoring import add_usage, get_chart_data, get_statistics

app = Flask(__name__)

DATABASE = "bettercal.db"


def create_db() -> sqlite3.Connection:
    if app.config["TESTING"]:
        db = sqlite3.connect(":memory:")
    else:
        db = sqlite3.connect(DATABASE)
        db.execute("PRAGMA journal_mode=WAL;")

    db.cursor().executescript(
        """
        CREATE TABLE IF NOT EXISTS statistics_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT DEFAULT (DATE('now')),
            token_hash TEXT NOT NULL,
            UNIQUE(date, token_hash)
        );
        """
    )
    db.commit()
    return db


def get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = create_db()
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# Preheat the statistics cache
get_chart_data(create_db())


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/statistics")
def statistic_page():
    statistic = get_statistics(get_db())
    chart_data = get_chart_data(get_db())
    return render_template(
        "statistics.html", statistic=statistic, chart_data=json.dumps(chart_data)
    )


@app.route("/static/<path:path>")
def static_asset(path):
    return send_from_directory("static", path)


@app.route("/verify")
def verify():
    url = request.args.get("url", "").strip()
    if url is None or url == "":
        return "Empty links don't work *surprised picatchu meme*", 400

    # A better error message if the submitted url is not of the icalendar but
    # of the html page itself.
    if url.startswith("https://tiss.tuwien.ac.at/events/personSchedule.xhtml"):
        return "Almost, the url we need is at the bottom of the page you submitted", 400

    # Inspecting the url
    scheme, loc, path, _, query, _ = urlparse(url)
    if not (
        scheme == "https"
        and loc == "tiss.tuwien.ac.at"
        and path == "/events/rest/calendar/personal"
    ):
        return "The url must point to the TISS calendar", 400
    if "token=" not in query:
        return "The complete calendar url must be submitted, including the token.", 400

    try:
        tiss.get_calendar(url)
    except requests.HTTPError:
        return "TISS rejected this url. Maybe the token is invalid?", 400
    except ConnectionError:
        return "Could not contact TISS. Maybe TISS is down?", 400
    except ValueError:
        return "TISS didn't return an ical file, did you paste the correct url?", 400
    except Exception:
        return "Something unexpected went wrong, maybe create an GitHub issue?", 500

    return "Ok"


@app.route("/personal.ics")
def icalendar():
    # If accessed from a browser render fallback
    if "text/html" in request.headers.get("Accept", ""):
        # The calendar shouldn't be opend in the but subscribed in your app
        return render_template("nobrowser.html"), 406

    token = request.args.get("token")
    if token is None:
        return "No token provided", 400

    locale = request.args.get("locale")
    if locale is None:
        return "No locale provided", 400

    is_google = "google" in request.args
    use_shorthand = "noshorthand" not in request.args

    url = f"https://tiss.tuwien.ac.at/events/rest/calendar/personal?token={token}&locale={locale}"
    cal = tiss.get_calendar(url)
    cal = improve_calendar(
        cal,
        google_cal=is_google,
        use_shorthand=use_shorthand,
        locale=locale,
    )
    body = cal.to_ical()

    add_usage(get_db(), token)

    return body, 200, {"Content-Type": "text/calendar; charset=utf-8"}
