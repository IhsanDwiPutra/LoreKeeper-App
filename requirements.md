# Requirements: LoreKeeper App

## Deskripsi Singkat
Aplikasi web internal untuk mencatat dan mengorganisir elemen cerita dan event (kejadian) untuk pengembangan game.

## Fitur Utama
1. **Sistem Manajemen Lore:**
   - Pengguna dapat menambahkan, mengedit, dan menghapus catatan (Entri) berupa Teks.
   - Setiap Entri memiliki atribut: "Judul", "Kategori" (Karakter, Lokasi, Item, Misteri), dan "Isi Cerita".
2. **Timeline Event:**
   - Pengguna dapat membuat urutan event.
   - Setiap event memiliki atribut: "Nama Event", "Lokasi", dan "Kondisi Trigger" (misal: "Pemain mengambil kunci").
3. **Antarmuka (UI):**
   - Menggunakan tema gelap (Dark Mode) secara default agar nyaman di mata.
   - Tampilan sederhana dengan *sidebar* untuk navigasi antar kategori.
4. **Fitur Moodboard (Media Referensi):**
   - Pengguna dapat mengunggah (upload) file gambar (JPG/PNG) dan file audio (MP3/WAV) ke dalam setiap Entri Lore.
   - Pada halaman detail atau daftar Entri, tampilkan *preview* gambar tersebut dan sediakan *mini audio player* (`<audio controls>`) untuk memutar efek suara secara langsung.
5. **Export Data Game-Ready:**
   - Sediakan tombol "Export to Game (JSON)" yang mudah diakses di navigasi atau header.
   - Saat tombol diklik, sistem akan mengunduh sebuah file `.json` yang berisi seluruh data "Entri Lore" dan "Timeline Event" dari database, terstruktur dengan rapi agar siap dibaca oleh game engine.
6. **Manajemen Timeline Event (CRUD):**
   - Fungsikan menu "Timeline Event" di sidebar agar membuka halaman khusus pengelola event.
   - Pengguna dapat melakukan Create, Read, Update, dan Delete data Event.
   - Form input Event harus memiliki field: "Nama Event" (contoh: Lampu Lorong Padam), "Lokasi" (teks tempat kejadian), dan "Kondisi Trigger" (contoh: Has_Rusty_Key == true).
7. **Manajemen Game Variables (Player State):**
   - Tambahkan menu "Game Variables" di sidebar untuk mengelola status global atau inventaris pemain.
   - Pengguna dapat melakukan Create, Read, Update, dan Delete (CRUD) data variabel.
   - Setiap variabel wajib memiliki atribut: "Nama Variabel" (contoh: Player_Sanity, Has_Rusty_Key), "Tipe Data" (pilihan dropdown: Integer, Boolean, String), dan "Nilai Default" (contoh: 100, false).