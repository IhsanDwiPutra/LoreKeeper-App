# System Design: LoreKeeper App

## Tech Stack
- Frontend: HTML, CSS, JavaScript sederhana.
- Backend: Python (menggunakan framework Flask atau FastAPI).
- Database: SQLite (karena ini aplikasi lokal dan privat, SQLite sangat ringan dan cukup).

## Struktur Database
Tabel `LoreEntry`:
- id (Integer, Primary Key)
- title (String)
- category (String)
- content (Text)

Update Tabel `LoreEntry` (Tambahan Kolom):
- image_path (String, nullable) - Untuk menyimpan lokasi file gambar.
- audio_path (String, nullable) - Untuk menyimpan lokasi file audio.

Struktur Folder Tambahan:
- Buat folder `static/uploads` untuk menyimpan file media yang diunggah pengguna.

Tabel `GameEvent`:
- id (Integer, Primary Key)
- event_name (String)
- location (String)
- trigger_condition (String)

## Tambahan Struktur Database untuk Variabel
Tabel `GameVariable`:
- id (Integer, Primary Key)
- name (String, Unique)
- var_type (String)
- default_value (String)

## Update Endpoint Export
- Endpoint `GET /api/export` harus diperbarui agar ikut menarik seluruh data dari tabel `GameVariable` dan menyisipkannya ke dalam struktur response JSON dengan key `"game_variables"`.

## Tambahan Endpoint API (Export)
- `GET /api/export` : Mengambil seluruh isi tabel `LoreEntry` dan `GameEvent`, menggabungkannya ke dalam satu format JSON terpusat, dan mengembalikannya sebagai file unduhan (attachment).

## Update UI & Routing untuk Event
- Frontend: Buat file `templates/events.html` dengan desain *dark mode* yang senada dengan halaman utama. Gunakan JavaScript Fetch API agar proses submit lancar tanpa *reload*.
- Backend: Pastikan endpoint CRUD untuk tabel `GameEvent` sudah beroperasi penuh di `app.py`.