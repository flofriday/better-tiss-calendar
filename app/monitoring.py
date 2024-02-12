import hashlib
from dataclasses import dataclass
from sqlite3 import Connection
from typing import Tuple


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
    total_users: int
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

    # Get all users
    cursor.execute(
        """SELECT COUNT(DISTINCT token_hash) AS unique_users
        FROM statistics;"""
    )
    total_users = cursor.fetchone()[0]

    # Get total number of rows
    cursor.execute("SELECT COUNT(*) FROM statistics")
    total_rows = cursor.fetchone()[0]

    return statistic(daily_users, monthly_users, total_users, total_rows)


def get_chart_data(db: Connection) -> list[Tuple[str, int]]:
    # Get daily active users
    cursor = db.cursor()
    cursor.execute(
        """
            SELECT strftime('%Y-%m-%d', s.date) AS day,
                    COUNT(DISTINCT token_hash) AS 'daily',
                    (SELECT COUNT(DISTINCT token_hash)
                    FROM statistics s2
                    WHERE Date(s2.date) <= s.date 
                    AND s2.date >= DATE( s.date, '-30 days')
                ) AS 'monbthly',
                (SELECT COUNT(DISTINCT token_hash)
                    FROM statistics s3
                    WHERE Date(s3.date) <=  s.date
                ) AS 'total'
            FROM statistics s
            GROUP BY day
            ORDER BY day 
        """
    )
    rows = cursor.fetchall()
    return rows
