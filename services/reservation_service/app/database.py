from contextlib import contextmanager

import psycopg

from .config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS reservations (
    confirmation_id TEXT PRIMARY KEY,
    ota_partner TEXT NOT NULL,
    hotel_chain_id TEXT NOT NULL,
    property_id TEXT NOT NULL,
    hotel_tier TEXT NOT NULL,
    guest_name TEXT NOT NULL,
    room_type TEXT NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    guest_count INTEGER NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


@contextmanager
def get_connection():
    with psycopg.connect(settings.database_url) as conn:
        yield conn


def initialize_schema() -> None:
    with get_connection() as conn:
        conn.execute(SCHEMA)
        conn.commit()


def insert_reservation(confirmation_id: str, reservation) -> None:
    sql = """
    INSERT INTO reservations (
        confirmation_id, ota_partner, hotel_chain_id, property_id, hotel_tier,
        guest_name, room_type, check_in, check_out, guest_count, total_amount, status
    )
    VALUES (
        %(confirmation_id)s, %(ota_partner)s, %(hotel_chain_id)s, %(property_id)s,
        %(hotel_tier)s, %(guest_name)s, %(room_type)s, %(check_in)s, %(check_out)s,
        %(guest_count)s, %(total_amount)s, %(status)s
    );
    """
    payload = reservation.model_dump()
    payload["confirmation_id"] = confirmation_id
    payload["hotel_tier"] = reservation.hotel_tier.value
    payload["status"] = "CONFIRMED"

    with get_connection() as conn:
        conn.execute(sql, payload)
        conn.commit()


def fetch_reservation(confirmation_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM reservations WHERE confirmation_id = %s;",
            (confirmation_id,),
        ).fetchone()
        if not row:
            return None
        columns = [desc.name for desc in conn.execute("SELECT * FROM reservations LIMIT 0").description]
        return dict(zip(columns, row))


def database_ready() -> bool:
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1;")
        return True
    except Exception:
        return False

