from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "camera_data.db")


# ---------- Database ----------

def db_connection():
    return sqlite3.connect(DB_FILE)


def create_table():
    with db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                police_station TEXT UNIQUE,
                camera_type TEXT,
                camera_status TEXT
            )
        """)


@app.on_event("startup")
def startup():
    create_table()


# ---------- Routes ----------

@app.get("/")
def root():
    return {"message": "Camera Monitoring API Running"}


@app.get("/cameras")
def get_cameras():
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT police_station, camera_type, camera_status FROM cameras"
        ).fetchall()

    return [
        {"Police Station": r[0], "Camera Type": r[1], "Camera Status": r[2]}
        for r in rows
    ]


@app.get("/cameras-table", response_class=HTMLResponse)
def show_table():
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT police_station, camera_type, camera_status FROM cameras"
        ).fetchall()

    table_rows = "".join(
        f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td></tr>"
        for r in rows
    )

    return f"""
    <html>
    <head>
        <title>Camera Status</title>
        <style>
            table {{border-collapse: collapse; width: 80%; margin: 20px auto;}}
            th, td {{border: 1px solid black; padding: 8px; text-align: center;}}
            th {{background-color: #f2f2f2;}}
        </style>
    </head>
    <body>
        <h2 style='text-align:center;'>Police Camera Status</h2>
        <table>
            <tr>
                <th>Police Station</th>
                <th>Camera Type</th>
                <th>Camera Status</th>
            </tr>
            {table_rows}
        </table>
        <br>
        <div style="text-align:center;">
            <a href="/update-form">Update Camera</a>
        </div>
    </body>
    </html>
    """


@app.get("/update-form", response_class=HTMLResponse)
def update_form():
    return """
    <html>
    <body>
        <h2>Update Camera Status</h2>
        <form action="/update-camera" method="post">
            Police Station: <input type="text" name="station"><br><br>
            Camera Type: <input type="text" name="type"><br><br>
            Camera Status:
            <select name="status">
                <option value="ONLINE">ONLINE</option>
                <option value="OFFLINE">OFFLINE</option>
            </select><br><br>
            <button type="submit">Update</button>
        </form>
    </body>
    </html>
    """


@app.post("/update-camera")
def update_camera(
    station: str = Form(...),
    type: str = Form(...),
    status: str = Form(...)
):
    station = station.strip().title()
    type = type.strip().upper()
    status = status.strip().upper()

    with db_connection() as conn:
        conn.execute("""
            INSERT INTO cameras (police_station, camera_type, camera_status)
            VALUES (?, ?, ?)
            ON CONFLICT(police_station)
            DO UPDATE SET
                camera_type=excluded.camera_type,
                camera_status=excluded.camera_status
        """, (station, type, status))

    return RedirectResponse(url="/cameras-table", status_code=303)


# ---------- Run Server ----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)