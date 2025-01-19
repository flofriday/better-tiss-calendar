from datetime import date
import hashlib
from dataclasses import dataclass
from sqlite3 import Connection
from typing import Tuple


def add_usage(db: Connection, token: str):
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    db.cursor().execute(
        "INSERT OR IGNORE INTO statistics_daily (token_hash) VALUES (?)",
        (hashed_token,),
    )
    db.commit()


@dataclass
class statistic:
    daily_users: int
    monthly_users: int
    total_users: int


def get_statistics(db: Connection) -> statistic:
    # Get daily active users
    cursor = db.cursor()
    cursor.execute(
        """SELECT COUNT(*)
        FROM statistics_daily
        WHERE date == DATE('now');"""
    )
    daily_users = cursor.fetchone()[0]

    # Get monthly active users
    cursor.execute(
        """SELECT COUNT(DISTINCT token_hash) AS unique_active_users
        FROM statistics_daily
        WHERE date >= DATE('now', '-30 days');"""
    )
    monthly_users = cursor.fetchone()[0]

    # Get all users
    cursor.execute(
        """SELECT COUNT(DISTINCT token_hash) AS unique_users
        FROM statistics_daily;"""
    )
    total_users = cursor.fetchone()[0]

    return statistic(daily_users, monthly_users, total_users)


# Only the usage for today will change, so we can cache all past days.
chart_cache: list[Tuple[str, int, int, int]] = []


def get_chart_data(db: Connection) -> list[Tuple[str, int, int, int]]:
    global chart_cache
    since = chart_cache[-1][0] if len(chart_cache) > 0 else None

    # Fetch the newest data
    new_data = get_chart_data_since(db, since)
    result = chart_cache + new_data

    # Update the cache (never store the last day because we don't trust it)
    # Well the day is not over so it will probably change.
    chart_cache += new_data[:-1]

    return result


def get_chart_data_since(
    db: Connection, since: str | None = None
) -> list[Tuple[str, int, int, int]]:
    if since is None:
        # This is just any day far in the past but, the exact day is just the day before
        # it went into production.
        since = "2023-07-16"

    # Get daily active users
    cursor = db.cursor()
    cursor.execute(
        """
            SELECT s.date AS day,
                    COUNT(*) AS 'daily',
                    (SELECT COUNT(DISTINCT token_hash)
                    FROM statistics_daily s2
                    WHERE s2.date <= s.date
                    AND s2.date >= DATE( s.date, '-30 days')
                ) AS 'monbthly',
                (SELECT COUNT(DISTINCT token_hash)
                    FROM statistics_daily s3
                    WHERE s3.date <=  s.date
                ) AS 'total'
            FROM statistics_daily s
            WHERE day > ?
            GROUP BY day
            ORDER BY day
        """,
        (since,),
    )
    rows = cursor.fetchall()
    return rows
