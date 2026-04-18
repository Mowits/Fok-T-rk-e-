from datetime import datetime


def add_or_update_med(conn, user: str, name: str, time_hm: str) -> None:
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM med_routines WHERE user = ? AND name = ?",
        (user, name),
    )
    row = cur.fetchone()
    if row:
        conn.execute(
            "UPDATE med_routines SET time_hm = ?, enabled = 1 WHERE id = ?",
            (time_hm, row[0]),
        )
    else:
        conn.execute(
            "INSERT INTO med_routines (user, name, time_hm) VALUES (?, ?, ?)",
            (user, name, time_hm),
        )
    conn.commit()


def disable_med(conn, user: str, name: str) -> None:
    conn.execute(
        "UPDATE med_routines SET enabled = 0 WHERE user = ? AND name = ?",
        (user, name),
    )
    conn.commit()


def fetch_due_meds(conn, now_local: datetime):
    hm = now_local.strftime("%H:%M")
    today = now_local.strftime("%Y-%m-%d")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user, name, time_hm, last_date
        FROM med_routines
        WHERE enabled = 1 AND time_hm = ?
        """,
        (hm,),
    )
    rows = []
    for rid, user, name, time_hm, last_date in cur.fetchall():
        if last_date != today:
            rows.append((rid, user, name))
    return rows


def mark_med_done_today(conn, med_id: int, now_local: datetime) -> None:
    today = now_local.strftime("%Y-%m-%d")
    conn.execute(
        "UPDATE med_routines SET last_date = ? WHERE id = ?",
        (today, med_id),
    )
    conn.commit()


def fetch_user_active_meds(conn, user: str):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name, time_hm, last_date
        FROM med_routines
        WHERE enabled = 1 AND user = ?
        ORDER BY time_hm ASC, name ASC
        """,
        (user,),
    )
    return cur.fetchall()
