from pathlib import Path
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "rentals.db"
UPLOAD_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "mp4", "mov"}

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-before-real-use"
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30 MB


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                area TEXT NOT NULL,
                address TEXT,
                maps_url TEXT,
                property_type TEXT NOT NULL,
                monthly_rent INTEGER,
                deposit INTEGER,
                owner_name TEXT NOT NULL,
                owner_phone TEXT NOT NULL,
                owner_permission TEXT NOT NULL DEFAULT 'Pending',
                brokerage_terms TEXT,
                facilities TEXT,
                media_filename TEXT,
                status TEXT NOT NULL DEFAULT 'Available',
                created_at TEXT NOT NULL
            )
        """)
        # Automatically add maps_url column if the table already existed without it
        cursor = conn.execute("PRAGMA table_info(properties)")
        columns = [row[1] for row in cursor.fetchall()]
        if "maps_url" not in columns:
            conn.execute("ALTER TABLE properties ADD COLUMN maps_url TEXT")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def dashboard():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
        available = conn.execute(
            "SELECT COUNT(*) FROM properties WHERE status = 'Available'"
        ).fetchone()[0]
        occupied = conn.execute(
            "SELECT COUNT(*) FROM properties WHERE status = 'Occupied'"
        ).fetchone()[0]
        latest = conn.execute(
            "SELECT * FROM properties ORDER BY id DESC LIMIT 5"
        ).fetchall()
    return render_template(
        "dashboard.html", total=total, available=available,
        occupied=occupied, latest=latest
    )


@app.route("/properties")
def properties():
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    sql = "SELECT * FROM properties WHERE 1=1"
    params = []
    if search:
        like = f"%{search}%"
        sql += """ AND (property_code LIKE ? OR title LIKE ? OR area LIKE ?
                   OR owner_name LIKE ? OR owner_phone LIKE ?)"""
        params.extend([like, like, like, like, like])
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id DESC"
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return render_template("properties.html", properties=rows, q=search, status=status)


@app.route("/properties/add", methods=["GET", "POST"])
def add_property():
    if request.method == "POST":
        data = request.form
        required = ["property_code", "title", "area", "property_type",
                    "owner_name", "owner_phone"]
        if any(not data.get(field, "").strip() for field in required):
            flash("Please fill in all required fields.", "error")
            return render_template("property_form.html", item=None)

        media_filename = None
        media = request.files.get("media")
        if media and media.filename:
            if not allowed_file(media.filename):
                flash("Use an image or video file (JPG, PNG, WEBP, MP4, MOV).", "error")
                return render_template("property_form.html", item=None)
            # Use a generated safe filename rather than trusting the uploaded name.
            extension = media.filename.rsplit(".", 1)[1].lower()
            media_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{extension}"
            media.save(UPLOAD_DIR / media_filename)

        try:
            with get_db() as conn:
                conn.execute("""
                    INSERT INTO properties (
                        property_code, title, area, address, maps_url, property_type,
                        monthly_rent, deposit, owner_name, owner_phone,
                        owner_permission, brokerage_terms, facilities,
                        media_filename, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["property_code"].strip().upper(), data["title"].strip(),
                    data["area"].strip(), data.get("address", "").strip(),
                    data.get("maps_url", "").strip(),
                    data["property_type"], to_int(data.get("monthly_rent")),
                    to_int(data.get("deposit")), data["owner_name"].strip(),
                    data["owner_phone"].strip(), data.get("owner_permission", "Pending"),
                    data.get("brokerage_terms", "").strip(),
                    data.get("facilities", "").strip(), media_filename,
                    data.get("status", "Available"), datetime.now().isoformat(timespec="minutes")
                ))
        except sqlite3.IntegrityError:
            flash("That Property ID already exists. Please use a unique ID.", "error")
            return render_template("property_form.html", item=None)

        flash("Property saved successfully.", "success")
        return redirect(url_for("properties"))

    return render_template("property_form.html", item=None)


@app.route("/properties/<int:property_id>/edit", methods=["GET", "POST"])
def edit_property(property_id):
    with get_db() as conn:
        item = conn.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()
    if item is None:
        flash("Property not found.", "error")
        return redirect(url_for("properties"))

    if request.method == "POST":
        data = request.form
        required = ["property_code", "title", "area", "property_type",
                    "owner_name", "owner_phone"]
        if any(not data.get(field, "").strip() for field in required):
            flash("Please fill in all required fields.", "error")
            return render_template("property_form.html", item=item)

        media_filename = item["media_filename"]
        media = request.files.get("media")
        if media and media.filename:
            if not allowed_file(media.filename):
                flash("Use an image or video file (JPG, PNG, WEBP, MP4, MOV).", "error")
                return render_template("property_form.html", item=item)
            extension = media.filename.rsplit(".", 1)[1].lower()
            new_media_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{extension}"
            media.save(UPLOAD_DIR / new_media_filename)
            # Remove old media file if a new one is uploaded
            if media_filename:
                old_path = UPLOAD_DIR / media_filename
                if old_path.exists():
                    old_path.unlink()
            media_filename = new_media_filename

        try:
            with get_db() as conn:
                conn.execute("""
                    UPDATE properties SET
                        property_code = ?, title = ?, area = ?, address = ?,
                        maps_url = ?, property_type = ?, monthly_rent = ?,
                        deposit = ?, owner_name = ?, owner_phone = ?,
                        owner_permission = ?, brokerage_terms = ?, facilities = ?,
                        media_filename = ?, status = ?
                    WHERE id = ?
                """, (
                    data["property_code"].strip().upper(), data["title"].strip(),
                    data["area"].strip(), data.get("address", "").strip(),
                    data.get("maps_url", "").strip(),
                    data["property_type"], to_int(data.get("monthly_rent")),
                    to_int(data.get("deposit")), data["owner_name"].strip(),
                    data["owner_phone"].strip(), data.get("owner_permission", "Pending"),
                    data.get("brokerage_terms", "").strip(),
                    data.get("facilities", "").strip(), media_filename,
                    data.get("status", "Available"), property_id
                ))
        except sqlite3.IntegrityError:
            flash("That Property ID is already used by another property. Please choose a unique ID.", "error")
            return render_template("property_form.html", item=item)

        flash("Property details updated successfully.", "success")
        return redirect(url_for("property_detail", property_id=property_id))

    return render_template("property_form.html", item=item)


def to_int(value):
    value = (value or "").strip()
    return int(value) if value.isdigit() else None


@app.route("/properties/<int:property_id>")
def property_detail(property_id):
    with get_db() as conn:
        item = conn.execute(
            "SELECT * FROM properties WHERE id = ?", (property_id,)
        ).fetchone()
    if item is None:
        flash("Property not found.", "error")
        return redirect(url_for("properties"))
    return render_template("property_detail.html", item=item)


@app.route("/properties/<int:property_id>/status", methods=["POST"])
def update_status(property_id):
    new_status = request.form.get("status", "Available")
    if new_status not in {"Available", "Occupied", "On Hold", "Needs Verification"}:
        flash("Invalid status.", "error")
        return redirect(url_for("property_detail", property_id=property_id))
    with get_db() as conn:
        conn.execute("UPDATE properties SET status = ? WHERE id = ?",
                     (new_status, property_id))
    flash("Property status updated.", "success")
    return redirect(url_for("property_detail", property_id=property_id))


@app.route("/properties/<int:property_id>/delete", methods=["POST"])
def delete_property(property_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT media_filename FROM properties WHERE id = ?", (property_id,)
        ).fetchone()
        conn.execute("DELETE FROM properties WHERE id = ?", (property_id,))
    if row and row["media_filename"]:
        media_path = UPLOAD_DIR / row["media_filename"]
        if media_path.exists():
            media_path.unlink()
    flash("Property record deleted.", "success")
    return redirect(url_for("properties"))


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    # Files are only served through this local app; do not upload private documents here.
    from flask import send_from_directory
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == "__main__":
    UPLOAD_DIR.mkdir(exist_ok=True)
    init_db()
    app.run(debug=True)
