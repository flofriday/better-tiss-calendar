from dataclasses import dataclass
from sqlite3 import Connection
import hashlib


def add_usage(db: Connection, token: str):
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    db.cursor().execute(
        "INSERT INTO statistics (token_hash) VALUES (?)", (hashed_token,)
    )
    db.commit()


@dataclass
class statistic:
    daily_users: int
    monthly_users: int
    total_usages: int


def get_statistics(db: Connection) -> statistic:
    # Get daily active users
    cursor = db.cursor()
    cursor.execute(
        """SELECT COUNT(DISTINCT token_hash) AS unique_active_users
        FROM statistics
        WHERE date >= DATETIME('now', '-1 days');"""
    )
    daily_users = cursor.fetchone()[0]

    # Get monthly active users
    cursor.execute(
        """SELECT COUNT(DISTINCT token_hash) AS unique_active_users
        FROM statistics
        WHERE date >= DATETIME('now', '-30 days');"""
    )
    monthly_users = cursor.fetchone()[0]

    # Get total number of rows
    cursor.execute("SELECT COUNT(*) FROM statistics")
    total_rows = cursor.fetchone()[0]

    return statistic(daily_users, monthly_users, total_rows)
