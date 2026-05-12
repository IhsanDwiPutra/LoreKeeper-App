import json
import os
import uuid
from datetime import datetime, timezone

from flask import Flask, Response, jsonify, request, render_template
from werkzeug.utils import secure_filename

from database import init_db, get_connection

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Upload configuration
# ---------------------------------------------------------------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav"}


def _allowed_extension(filename: str, allowed: set) -> bool:
    """Return True jika ekstensi file ada di set yang diizinkan."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _save_upload(file_storage, allowed_extensions: set) -> str:
    """
    Validasi ekstensi, buat nama file unik, simpan ke UPLOAD_FOLDER.
    Kembalikan path relatif (misal 'uploads/abc123.jpg').
    Raise ValueError jika ekstensi tidak diizinkan.
    """
    original_name = secure_filename(file_storage.filename or "")
    if not _allowed_extension(original_name, allowed_extensions):
        raise ValueError(f"Ekstensi file tidak diizinkan: '{original_name}'")

    ext = original_name.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file_storage.save(save_path)
    return f"uploads/{unique_name}"


def _delete_file_if_exists(relative_path: str | None) -> None:
    """Hapus file dari disk jika path-nya ada dan file-nya memang ada."""
    if not relative_path:
        return
    abs_path = os.path.join(os.path.dirname(__file__), "static", relative_path)
    if os.path.isfile(abs_path):
        os.remove(abs_path)

# Inisialisasi database saat aplikasi pertama kali dijalankan
with app.app_context():
    init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/events")
def events():
    return render_template("events.html")


# ---------------------------------------------------------------------------
# LoreEntry CRUD Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/lore", methods=["GET"])
def get_all_lore():
    """Ambil semua LoreEntry. Mendukung filter opsional via query param ?category=."""
    category = request.args.get("category")
    with get_connection() as conn:
        if category:
            rows = conn.execute(
                "SELECT * FROM LoreEntry WHERE category = ? ORDER BY id",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM LoreEntry ORDER BY id"
            ).fetchall()
    return jsonify([dict(row) for row in rows]), 200


@app.route("/api/lore/<int:entry_id>", methods=["GET"])
def get_lore(entry_id):
    """Ambil satu LoreEntry berdasarkan id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM LoreEntry WHERE id = ?", (entry_id,)
        ).fetchone()
    if row is None:
        return jsonify({"error": "LoreEntry tidak ditemukan."}), 404
    return jsonify(dict(row)), 200


@app.route("/api/lore", methods=["POST"])
def create_lore():
    """Buat LoreEntry baru. Body JSON: {title, category, content}."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body harus berupa JSON."}), 400

    title = (data.get("title") or "").strip()
    category = (data.get("category") or "").strip()
    content = (data.get("content") or "").strip()

    if not title or not category or not content:
        return jsonify({"error": "Field 'title', 'category', dan 'content' wajib diisi."}), 400

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO LoreEntry (title, category, content) VALUES (?, ?, ?)",
            (title, category, content),
        )
        new_id = cursor.lastrowid
        conn.commit()
        row = conn.execute(
            "SELECT * FROM LoreEntry WHERE id = ?", (new_id,)
        ).fetchone()

    return jsonify(dict(row)), 201


@app.route("/api/lore/<int:entry_id>", methods=["PUT"])
def update_lore(entry_id):
    """Update LoreEntry. Body JSON: {title?, category?, content?}."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body harus berupa JSON."}), 400

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM LoreEntry WHERE id = ?", (entry_id,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "LoreEntry tidak ditemukan."}), 404

        existing = dict(row)
        title = (data.get("title") or existing["title"]).strip()
        category = (data.get("category") or existing["category"]).strip()
        content = (data.get("content") or existing["content"]).strip()

        if not title or not category or not content:
            return jsonify({"error": "Field 'title', 'category', dan 'content' tidak boleh kosong."}), 400

        conn.execute(
            "UPDATE LoreEntry SET title = ?, category = ?, content = ? WHERE id = ?",
            (title, category, content, entry_id),
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM LoreEntry WHERE id = ?", (entry_id,)
        ).fetchone()

    return jsonify(dict(updated)), 200


@app.route("/api/lore/<int:entry_id>/upload", methods=["POST"])
def upload_media(entry_id):
    """
    Upload file gambar dan/atau audio ke LoreEntry.

    Multipart form-data fields (keduanya opsional):
      image – file JPG/PNG
      audio – file MP3/WAV

    Setidaknya satu field harus ada. Mengembalikan LoreEntry yang sudah diperbarui.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM LoreEntry WHERE id = ?", (entry_id,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "LoreEntry tidak ditemukan."}), 404

        existing = dict(row)

    image_file = request.files.get("image")
    audio_file = request.files.get("audio")

    if not image_file and not audio_file:
        return jsonify({"error": "Setidaknya satu file ('image' atau 'audio') harus dikirim."}), 400

    new_image_path = existing.get("image_path")
    new_audio_path = existing.get("audio_path")

    # --- Proses file gambar ---
    if image_file and image_file.filename:
        try:
            new_image_path = _save_upload(image_file, ALLOWED_IMAGE_EXTENSIONS)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    # --- Proses file audio ---
    if audio_file and audio_file.filename:
        try:
            new_audio_path = _save_upload(audio_file, ALLOWED_AUDIO_EXTENSIONS)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    # --- Simpan path ke database ---
    with get_connection() as conn:
        conn.execute(
            "UPDATE LoreEntry SET image_path = ?, audio_path = ? WHERE id = ?",
            (new_image_path, new_audio_path, entry_id),
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM LoreEntry WHERE id = ?", (entry_id,)
        ).fetchone()

    return jsonify(dict(updated)), 200


@app.route("/api/lore/<int:entry_id>", methods=["DELETE"])
def delete_lore(entry_id):
    """Hapus LoreEntry berdasarkan id, termasuk file media dari disk."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM LoreEntry WHERE id = ?", (entry_id,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "LoreEntry tidak ditemukan."}), 404

        entry = dict(row)

        # Hapus file media dari disk sebelum menghapus record
        _delete_file_if_exists(entry.get("image_path"))
        _delete_file_if_exists(entry.get("audio_path"))

        conn.execute("DELETE FROM LoreEntry WHERE id = ?", (entry_id,))
        conn.commit()

    return jsonify({"message": f"LoreEntry {entry_id} berhasil dihapus."}), 200


# ---------------------------------------------------------------------------
# GameEvent CRUD Endpoints
# ---------------------------------------------------------------------------

def _get_event_with_conditions(conn, event_id: int) -> dict | None:
    """
    Ambil satu GameEvent beserta daftar kondisinya dari tabel EventCondition.
    Kembalikan dict dengan key 'conditions' berisi list kondisi, atau None jika tidak ditemukan.
    """
    row = conn.execute(
        "SELECT id, event_name, location FROM GameEvent WHERE id = ?", (event_id,)
    ).fetchone()
    if row is None:
        return None

    condition_rows = conn.execute(
        "SELECT id, variable_name, operator, target_value "
        "FROM EventCondition WHERE event_id = ? ORDER BY id",
        (event_id,),
    ).fetchall()

    event = dict(row)
    event["conditions"] = [dict(c) for c in condition_rows]
    return event


@app.route("/api/events", methods=["GET"])
def get_all_events():
    """Ambil semua GameEvent beserta kondisinya, diurutkan berdasarkan id."""
    with get_connection() as conn:
        event_rows = conn.execute(
            "SELECT id, event_name, location FROM GameEvent ORDER BY id"
        ).fetchall()
        result = []
        for row in event_rows:
            event = dict(row)
            condition_rows = conn.execute(
                "SELECT id, variable_name, operator, target_value "
                "FROM EventCondition WHERE event_id = ? ORDER BY id",
                (event["id"],),
            ).fetchall()
            event["conditions"] = [dict(c) for c in condition_rows]
            result.append(event)
    return jsonify(result), 200


@app.route("/api/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    """Ambil satu GameEvent beserta kondisinya berdasarkan id."""
    with get_connection() as conn:
        event = _get_event_with_conditions(conn, event_id)
    if event is None:
        return jsonify({"error": "GameEvent tidak ditemukan."}), 404
    return jsonify(event), 200


@app.route("/api/events", methods=["POST"])
def create_event():
    """
    Buat GameEvent baru beserta kondisi-kondisinya dalam satu transaksi.
    Body JSON: {event_name, location, conditions?: [{variable_name, operator, target_value}]}
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body harus berupa JSON."}), 400

    event_name = (data.get("event_name") or "").strip()
    location   = (data.get("location") or "").strip()
    conditions = data.get("conditions") or []

    if not event_name or not location:
        return jsonify({"error": "Field 'event_name' dan 'location' wajib diisi."}), 400

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO GameEvent (event_name, location) VALUES (?, ?)",
            (event_name, location),
        )
        new_id = cursor.lastrowid

        for cond in conditions:
            variable_name = (cond.get("variable_name") or "").strip()
            operator      = (cond.get("operator") or "").strip()
            target_value  = (cond.get("target_value") or "").strip()
            if variable_name and operator:
                conn.execute(
                    "INSERT INTO EventCondition (event_id, variable_name, operator, target_value) "
                    "VALUES (?, ?, ?, ?)",
                    (new_id, variable_name, operator, target_value),
                )

        conn.commit()
        event = _get_event_with_conditions(conn, new_id)

    return jsonify(event), 201


@app.route("/api/events/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    """
    Update GameEvent dan ganti semua kondisinya sekaligus.
    Body JSON: {event_name?, location?, conditions?: [{variable_name, operator, target_value}]}
    Semua EventCondition lama untuk event ini akan dihapus dan diganti dengan yang baru.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body harus berupa JSON."}), 400

    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, event_name, location FROM GameEvent WHERE id = ?", (event_id,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "GameEvent tidak ditemukan."}), 404

        existing = dict(row)
        event_name = (data.get("event_name") or existing["event_name"]).strip()
        location   = (data.get("location") or existing["location"]).strip()
        conditions = data.get("conditions") or []

        if not event_name or not location:
            return jsonify({"error": "Field 'event_name' dan 'location' tidak boleh kosong."}), 400

        conn.execute(
            "UPDATE GameEvent SET event_name = ?, location = ? WHERE id = ?",
            (event_name, location, event_id),
        )

        # Hapus semua kondisi lama, lalu sisipkan yang baru
        conn.execute(
            "DELETE FROM EventCondition WHERE event_id = ?", (event_id,)
        )
        for cond in conditions:
            variable_name = (cond.get("variable_name") or "").strip()
            operator      = (cond.get("operator") or "").strip()
            target_value  = (cond.get("target_value") or "").strip()
            if variable_name and operator:
                conn.execute(
                    "INSERT INTO EventCondition (event_id, variable_name, operator, target_value) "
                    "VALUES (?, ?, ?, ?)",
                    (event_id, variable_name, operator, target_value),
                )

        conn.commit()
        event = _get_event_with_conditions(conn, event_id)

    return jsonify(event), 200


@app.route("/api/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    """Hapus GameEvent berdasarkan id. EventCondition terkait terhapus otomatis via CASCADE."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM GameEvent WHERE id = ?", (event_id,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "GameEvent tidak ditemukan."}), 404

        conn.execute("DELETE FROM GameEvent WHERE id = ?", (event_id,))
        conn.commit()

    return jsonify({"message": f"GameEvent {event_id} berhasil dihapus."}), 200


# ---------------------------------------------------------------------------
# GameVariable Page Route
# ---------------------------------------------------------------------------

@app.route("/variables")
def variables():
    return render_template("variables.html")


# ---------------------------------------------------------------------------
# GameVariable CRUD Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/variables", methods=["GET"])
def get_all_variables():
    """Ambil semua GameVariable, diurutkan berdasarkan id."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM GameVariable ORDER BY id"
        ).fetchall()
    return jsonify([dict(row) for row in rows]), 200


@app.route("/api/variables/<int:variable_id>", methods=["GET"])
def get_variable(variable_id):
    """Ambil satu GameVariable berdasarkan id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM GameVariable WHERE id = ?", (variable_id,)
        ).fetchone()
    if row is None:
        return jsonify({"error": "GameVariable tidak ditemukan."}), 404
    return jsonify(dict(row)), 200


@app.route("/api/variables", methods=["POST"])
def create_variable():
    """Buat GameVariable baru. Body JSON: {name, var_type, default_value}."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body harus berupa JSON."}), 400

    name          = (data.get("name") or "").strip()
    var_type      = (data.get("var_type") or "").strip()
    default_value = (data.get("default_value") or "").strip()

    if not name or not var_type or not default_value:
        return jsonify({"error": "Field 'name', 'var_type', dan 'default_value' wajib diisi."}), 400

    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO GameVariable (name, var_type, default_value) VALUES (?, ?, ?)",
                (name, var_type, default_value),
            )
            new_id = cursor.lastrowid
            conn.commit()
            row = conn.execute(
                "SELECT * FROM GameVariable WHERE id = ?", (new_id,)
            ).fetchone()
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            return jsonify({"error": f"Nama variabel '{name}' sudah digunakan."}), 409
        raise

    return jsonify(dict(row)), 201


@app.route("/api/variables/<int:variable_id>", methods=["PUT"])
def update_variable(variable_id):
    """Update GameVariable. Body JSON: {name?, var_type?, default_value?}."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body harus berupa JSON."}), 400

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM GameVariable WHERE id = ?", (variable_id,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "GameVariable tidak ditemukan."}), 404

        existing = dict(row)
        name          = (data.get("name") or existing["name"]).strip()
        var_type      = (data.get("var_type") or existing["var_type"]).strip()
        default_value = (data.get("default_value") or existing["default_value"]).strip()

        if not name or not var_type or not default_value:
            return jsonify({"error": "Field 'name', 'var_type', dan 'default_value' tidak boleh kosong."}), 400

        try:
            conn.execute(
                "UPDATE GameVariable SET name = ?, var_type = ?, default_value = ? WHERE id = ?",
                (name, var_type, default_value, variable_id),
            )
            conn.commit()
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                return jsonify({"error": f"Nama variabel '{name}' sudah digunakan."}), 409
            raise

        updated = conn.execute(
            "SELECT * FROM GameVariable WHERE id = ?", (variable_id,)
        ).fetchone()

    return jsonify(dict(updated)), 200


@app.route("/api/variables/<int:variable_id>", methods=["DELETE"])
def delete_variable(variable_id):
    """Hapus GameVariable berdasarkan id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM GameVariable WHERE id = ?", (variable_id,)
        ).fetchone()
        if row is None:
            return jsonify({"error": "GameVariable tidak ditemukan."}), 404

        conn.execute("DELETE FROM GameVariable WHERE id = ?", (variable_id,))
        conn.commit()

    return jsonify({"message": f"GameVariable {variable_id} berhasil dihapus."}), 200


# ---------------------------------------------------------------------------
# Export Endpoint
# ---------------------------------------------------------------------------

@app.route("/api/export", methods=["GET"])
def export_data():
    """
    Ekspor seluruh isi database sebagai file JSON yang bisa diunduh.

    Response headers:
      Content-Type        : application/json
      Content-Disposition : attachment; filename="lorekeeper_export.json"
    """
    with get_connection() as conn:
        lore_rows = conn.execute(
            "SELECT * FROM LoreEntry ORDER BY id"
        ).fetchall()
        event_rows = conn.execute(
            "SELECT id, event_name, location FROM GameEvent ORDER BY id"
        ).fetchall()
        var_rows = conn.execute(
            "SELECT * FROM GameVariable ORDER BY id"
        ).fetchall()

        # Sertakan kondisi untuk setiap event
        game_events = []
        for row in event_rows:
            event = dict(row)
            condition_rows = conn.execute(
                "SELECT id, variable_name, operator, target_value "
                "FROM EventCondition WHERE event_id = ? ORDER BY id",
                (event["id"],),
            ).fetchall()
            event["conditions"] = [dict(c) for c in condition_rows]
            game_events.append(event)

    payload = {
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lore_entries": [dict(row) for row in lore_rows],
        "game_events": game_events,
        "game_variables": [dict(row) for row in var_rows],
    }

    json_str = json.dumps(payload, indent=2, ensure_ascii=False)

    return Response(
        json_str,
        status=200,
        mimetype="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="lorekeeper_export.json"',
        },
    )


if __name__ == "__main__":
    app.run(debug=False)
