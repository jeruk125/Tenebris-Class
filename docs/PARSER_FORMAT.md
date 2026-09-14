# Tenebris-Class Markup Language

## 1. Apa itu Tenebris-Class Markup?
Tenebris-Class Markup adalah bahasa markup sederhana dan terstruktur yang digunakan oleh Tenebris-Class LMS untuk mem-parsing teks mentah menjadi konten pembelajaran interaktif. Format ini dirancang mudah dibaca manusia dan diproduksi oleh AI.

## 2. Tujuan Parser
Tujuan utama parser ini adalah:
* Mengubah konten teks dari AI menjadi struktur HTML yang rapi untuk ditampilkan.
* Memberikan struktur kuis (Multiple Choice dan Essay) yang valid bagi database.
* Memisahkan elemen konten spesifik (Dataset, Formula, dll) agar dapat di-render dengan fitur interaktif (seperti Copy to Excel).
* Memberikan deteksi error markup secara spesifik.

## 3. Syntax Dasar
Tag ditulis menggunakan tanda kurung siku `[TAG]` untuk pembuka dan `[/TAG]` untuk penutup.
Setiap tag pembuka harus memiliki tag penutup pasangannya.

## 4. Blocks Utama (Root Blocks)
Sistem ini menggunakan *Root Blocks* sebagai pembungkus utama konten:
* `[MATERIAL]` : Untuk konten materi biasa.
* `[EXERCISE]` : Untuk latihan soal atau tugas praktik.
* `[PROJECT]` : Untuk mini-project atau tugas akhir.
* `[QUIZ]` : Untuk kuis pilihan ganda atau esai.

Setiap file *harus* dibungkus oleh salah satu tag ini di tingkat paling atas.

## 5. Tag Spesifik (Nesting)
Berikut adalah daftar tag yang didukung di dalam `[MATERIAL]`, `[EXERCISE]`, dan `[PROJECT]`:

* `[TITLE]` : Judul materi/halaman.
* `[HEADING]` : Sub-judul materi.
* `[PARAGRAPH]` : Paragraf teks biasa. Bisa multiline.
* `[NOTE]` : Catatan penting untuk siswa.
* `[WARNING]` : Peringatan.
* `[SUMMARY]` : Rangkuman materi.
* `[EXAMPLE]` : Contoh penyelesaian.
* `[OBJECTIVE]` : Tujuan pembelajaran.
* `[STEPS]` dan `[STEP]` : Untuk langkah-langkah terstruktur.
* `[FORMULA]` : Menampilkan formula Excel.
* `[CODE]` : Menampilkan blok kode pemrograman.
* `[TABLE]` atau `[DATASET]` : Menampilkan tabel data yang dapat di-copy.
* `[TASKS]` dan `[TASK]` : Instruksi atau bagian tugas praktik.
* `[HINT]` : Petunjuk mengerjakan.
* `[EXPECTED]` : Output yang diharapkan.
* `[DESCRIPTION]` : Deskripsi project.
* `[REQUIREMENTS]` dan `[REQUIREMENT]` : Syarat wajib pengerjaan project.
* `[OUTPUT]` : Hasil project yang diminta.
* `[RUBRIC]` dan `[CRITERIA]` : Rubrik penilaian.

## 6. Table / Dataset Syntax
Gunakan `[DATASET]` atau `[TABLE]`. Data dipisahkan oleh karakter pipe `|`.
Baris pertama otomatis menjadi header (judul kolom).

Contoh:
```text
[DATASET]
Nama | Nilai | Status
Andi | 85 | Lulus
Budi | 65 | Remedial
[/DATASET]
```

## 7. Quiz Syntax
Kuis *harus* memiliki `[TYPE]` (`pilihan_ganda` atau `teks`).
Setiap pertanyaan dibungkus dengan `[QUESTION X]`.

Contoh Multiple Choice:
```text
[QUIZ]
[TYPE]pilihan_ganda[/TYPE]
[QUESTION 1]
[QUESTION]Berapa 1 + 1?[/QUESTION]
[OPTIONS]
A. 1
B. 2
C. 3
D. 4
[/OPTIONS]
[ANSWER]B[/ANSWER]
[/QUESTION 1]
[/QUIZ]
```

Contoh Essay:
```text
[QUIZ]
[TYPE]teks[/TYPE]
[QUESTION 1]
[QUESTION]Jelaskan fungsi rumus VLOOKUP pada Excel![/QUESTION]
[ANSWER]VLOOKUP mencari nilai pada sebuah kolom paling kiri dan mengambil nilai pada baris yang sama dari kolom lain.[/ANSWER]
[/QUESTION 1]
[/QUIZ]
```

## 8. Error Handling
Jika terdapat tag yang hilang, salah ketik, atau tidak ditutup, Parser tidak akan crash. Ia akan mengembalikan error structure:
`"Missing closing tag [/TITLE]"`
Atau jika ada tag aneh:
`"Unknown tag: [FOO]"`

## 9. Security Considerations
Seluruh text di-sanitize secara aman mencegah serangan XSS.
Jangan menggunakan HTML literal secara sembarangan, karakter `<`, `>`, dll, otomatis akan di-escape.

## 10. Backward Compatibility
Apabila teks tidak memiliki satupun tag root `[MATERIAL]`, `[EXERCISE]`, `[PROJECT]`, atau `[QUIZ]`, sistem otomatis menganggap teks tersebut ditulis dengan format parser lama. Data lama Anda 100% aman.

## 11. Contoh Full Material
```text
[MATERIAL]
[TITLE]Dasar Excel[/TITLE]
[HEADING]1. Pengenalan[/HEADING]
[PARAGRAPH]
Excel sangat mudah digunakan.
Mari kita praktik.
[/PARAGRAPH]
[NOTE]Selalu simpan pekerjaanmu dengan Ctrl+S.[/NOTE]
[DATASET]
Bulan | Pemasukan
Januari | 500000
[/DATASET]
[/MATERIAL]
```
