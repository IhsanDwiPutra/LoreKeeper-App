# Implementation Tasks

- [x] Task 1: Inisialisasi project Python dan setup virtual environment.
- [x] Task 2: Buat struktur database SQLite sesuai `design.md`.
- [x] Task 3: Buat endpoint backend (Python) untuk Create, Read, Update, Delete (CRUD) tabel `LoreEntry`.
- [x] Task 4: Buat halaman HTML statis dengan tema gelap.
- [x] Task 5: Hubungkan frontend dengan backend menggunakan JavaScript Fetch API.
- [x] Task 6: Buat folder `static/uploads` dan perbarui skema database SQLite `LoreEntry` untuk kolom media.
- [x] Task 7: Update endpoint backend (app.py) agar bisa menerima file upload, menyimpannya ke folder uploads, dan mencatat path-nya ke database.
- [x] Task 8: Update frontend HTML/JS agar memiliki form input file, serta menampilkan preview gambar dan pemutar audio di daftar lore.
- [x] Task 9: Buat endpoint backend `/api/export` di Flask untuk membungkus semua isi database menjadi response JSON file yang bisa diunduh.
- [x] Task 10: Tambahkan tombol "Export to Game (JSON)" di antarmuka HTML/JS utama yang akan memanggil endpoint tersebut dan memulai proses unduhan file di browser.
- [x] Task 11: Buat file `templates/events.html` dan hubungkan navigasi sidebar "Timeline Event" agar mengarah ke halaman ini.
- [x] Task 12: Buat logika endpoint backend (GET, POST, PUT, DELETE) di `app.py` untuk mengelola data tabel `GameEvent`.
- [x] Task 13: Pastikan data `GameEvent` yang baru diinput berhasil ter-export dan masuk ke dalam array `"game_events"` pada fitur Export JSON.