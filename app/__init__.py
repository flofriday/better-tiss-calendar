import json
import sqlite3

import requests
from flask import Flask, g, render_template, request, send_from_directory

import app.tiss as tiss
from app.format import improve_calendar
from app.monitoring import add_usage, get_chart_data, get_statistics

app = Flask(__name__)

DATABASE = "bettercal.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        if app.config["TESTING"]:
            db = g._database = sqlite3.connect(":memory:")
        else:
            db = g._database = sqlite3.connect(DATABASE)
            db.execute("PRAGMA journal_mode=WAL;")

        db.cursor().executescript(
            """
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT DEFAULT (DATETIME('now')),
                token_hash TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_date ON statistics (date);
            """
        )
        db.commit()
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


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
    url = request.args.get("url").strip()
    if url is None or url == "":
        return "No url provided", 400

    # A better error message if the submitted url is not of the icalendar but
    # of the html page itself.
    if url.startswith("https://tiss.tuwien.ac.at/events/personSchedule.xhtml"):
        return "Almost, the url we need is at the bottom of the page you submitted", 400

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
    except Exception:
        return "Something unexpected went wrong, maybe create an GitHub issue?", 500

    return "Ok"


@app.route("/personal.ics")
def icalendar():
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
