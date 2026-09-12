# Tenebris-Class

> A web-based Learning Management System (LMS) built with Flask for managing classes, learning materials, quizzes, students, and teachers.

**Tenebris-Class** adalah aplikasi Learning Management System (LMS) berbasis web yang dirancang untuk membantu proses pembelajaran antara **siswa, guru, dan administrator**.

Project ini dibuat menggunakan **Python Flask** dengan **SQLite** sebagai database dan menyediakan sistem pembelajaran berbasis mata pelajaran, pertemuan, materi, serta kuis.

---

## ✨ Features

### 👨‍🎓 Student

Siswa dapat:

* Membuat akun dan melakukan login
* Melihat mata pelajaran yang diikuti
* Melihat daftar pertemuan
* Membaca materi pembelajaran
* Mengikuti kuis
* Melihat hasil kuis
* Melihat riwayat percobaan kuis
* Melihat detail jawaban dan nilai kuis

### 👨‍🏫 Teacher

Guru dapat:

* Membuat dan mengelola mata pelajaran
* Membuat pertemuan pembelajaran
* Menambahkan dan mengedit materi
* Mengunggah file pendukung pembelajaran
* Membuat kuis
* Mengelola soal pilihan ganda dan soal esai
* Melihat hasil kuis siswa
* Memberikan nilai untuk soal esai
* Mengelola siswa dalam mata pelajaran
* Menyimpan materi ke dalam **Material Bank**
* Menyimpan kuis ke dalam **Quiz Bank**
* Mengimpor materi atau kuis yang telah disimpan sebelumnya

### 🛠️ Administrator

Administrator memiliki akses untuk:

* Mengelola akun guru
* Mengelola akun siswa
* Mengelola data pembelajaran
* Mengakses fitur administrasi yang tersedia dalam sistem

---

## 🧩 Learning Structure

Sistem pembelajaran Tenebris-Class menggunakan struktur:

```text
Subject
  │
  ├── Meeting 1
  │     ├── Material
  │     └── Quiz
  │
  ├── Meeting 2
  │     ├── Material
  │     └── Quiz
  │
  └── Meeting 3
        ├── Material
        └── Quiz
```

Dengan struktur tersebut, materi dan kuis dapat diorganisasikan berdasarkan **mata pelajaran → pertemuan → materi/kuis**.

---

## 📝 Quiz System

Tenebris-Class memiliki sistem kuis yang mendukung beberapa jenis soal.

### Multiple Choice

Soal pilihan ganda dapat diperiksa secara otomatis oleh sistem.

### Essay

Soal esai dapat dijawab oleh siswa dan kemudian diperiksa serta diberikan nilai oleh guru.

Hasil pengerjaan kuis disimpan sehingga siswa dapat melihat riwayat pengerjaan dan guru dapat melihat hasil siswa.

---

## 📚 Material & Quiz Bank

Salah satu fitur utama Tenebris-Class adalah sistem **Bank**.

Guru dapat menyimpan materi dan kuis yang sudah dibuat untuk digunakan kembali pada pembelajaran lain.

```text
Material
   ↓
Save to Bank
   ↓
Material Bank
   ↓
Import to another Meeting
```

Hal ini mengurangi kebutuhan guru untuk membuat ulang materi atau kuis yang sama.

---

## 🔐 User Roles

Tenebris-Class menggunakan sistem role-based access.

| Role    | Access                                                |
| ------- | ----------------------------------------------------- |
| `siswa` | Mengikuti pembelajaran dan mengerjakan kuis           |
| `guru`  | Mengelola pembelajaran, materi, kuis, dan hasil siswa |
| `admin` | Mengelola sistem dan akun pengguna                    |

Akses halaman tertentu dibatasi berdasarkan role pengguna yang sedang login.

---

## 🏗️ Project Structure

```text
Tenebris-Class/
│
├── app.py
├── extensions.py
├── models.py
├── parsers.py
├── requirements.txt
│
├── templates/
│   ├── ...
│
├── static/
│   └── css/
│       └── ...
│
├── test_app.py
├── test_parsers.py
│
└── README.md
```

### Main Files

#### `app.py`

Berisi aplikasi utama Flask, routing, autentikasi, dashboard, pengelolaan pembelajaran, materi, kuis, hasil kuis, dan administrasi.

#### `models.py`

Berisi model database menggunakan Flask-SQLAlchemy.

Beberapa model utama yang digunakan antara lain:

* `User`
* `Subject`
* `Meeting`
* `Material`
* `Quiz`
* `QuestionMCQ`
* `QuestionText`
* `QuizResult`
* `SavedCategory`
* `SavedMaterial`
* `SavedQuiz`

#### `parsers.py`

Berisi fungsi yang digunakan untuk memproses dan mengubah data mentah materi/kuis menjadi struktur yang dapat digunakan oleh aplikasi.

#### `extensions.py`

Berisi konfigurasi dan inisialisasi extension Flask yang digunakan oleh aplikasi.

#### `templates/`

Berisi halaman HTML yang digunakan sebagai antarmuka aplikasi.

#### `static/css/`

Berisi stylesheet untuk tampilan antarmuka aplikasi.

#### `test_app.py`

Berisi pengujian terhadap fungsi aplikasi.

#### `test_parsers.py`

Berisi pengujian terhadap sistem parser.

---

## 🛠️ Technologies

| Technology       | Purpose                      |
| ---------------- | ---------------------------- |
| Python           | Programming language         |
| Flask            | Web framework                |
| Flask-SQLAlchemy | Database ORM                 |
| Flask-Login      | User authentication          |
| Werkzeug         | Password hashing & utilities |
| SQLite           | Database                     |
| HTML             | Web structure                |
| CSS              | User interface               |

Dependencies utama project saat ini adalah Flask 3.0.0, Flask-SQLAlchemy 3.1.1, Flask-Login 0.6.3, dan Werkzeug 3.0.1.

---

## 🚀 Installation

### 1. Clone Repository

```bash
git clone https://github.com/jeruk125/Tenebris-Class.git
cd Tenebris-Class
```

### 2. Create Virtual Environment

Windows:

```bash
python -m venv venv
```

Activate:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Application

```bash
python app.py
```

Setelah aplikasi berjalan, buka:

```text
http://127.0.0.1:5000
```

---

## ⚙️ Configuration

Aplikasi menggunakan environment variable untuk beberapa konfigurasi penting.

Contohnya:

```text
SECRET_KEY
```

Jika tidak diberikan, aplikasi memiliki nilai default untuk development.

Untuk penggunaan production, disarankan memberikan `SECRET_KEY` melalui environment variable.

Contoh Windows:

```powershell
$env:SECRET_KEY="your-secret-key"
python app.py
```

---

## 🗄️ Database

Tenebris-Class menggunakan **SQLite** melalui Flask-SQLAlchemy.

Database digunakan untuk menyimpan antara lain:

* User
* Role
* Subject
* Meeting
* Material
* Quiz
* Questions
* Quiz Results
* Saved Materials
* Saved Quizzes

File database dapat dibuat/digunakan oleh aplikasi ketika sistem melakukan inisialisasi database.

---

## 📤 File Upload

Aplikasi menyediakan fitur upload file untuk mendukung materi pembelajaran.

Format file yang saat ini diperbolehkan:

```text
PNG
JPG
JPEG
GIF
PDF
MP4
```

Ukuran upload maksimum yang dikonfigurasi adalah **16 MB**.

File yang diunggah disimpan pada:

```text
static/uploads/
```

---

## 🧪 Testing

Project menyediakan file pengujian:

```bash
python -m pytest
```

Test utama terdapat pada:

```text
test_app.py
test_parsers.py
```

---

## 🔄 Application Flow

### Student Flow

```text
Register
   ↓
Login
   ↓
Student Dashboard
   ↓
Choose Subject
   ↓
Choose Meeting
   ↓
Read Material
   ↓
Take Quiz
   ↓
View Result
```

### Teacher Flow

```text
Login
   ↓
Teacher Dashboard
   ↓
Create Subject
   ↓
Create Meeting
   ↓
Create Material / Quiz
   ↓
Publish to Students
   ↓
Monitor Student Results
   ↓
Grade Essay
```

### Material Bank Flow

```text
Create Material
       ↓
Save to Bank
       ↓
Material Bank
       ↓
Select Material
       ↓
Import to Meeting
```

---

## 🎯 Project Goals

Tenebris-Class dikembangkan dengan beberapa tujuan:

1. Membuat sistem pembelajaran yang sederhana dan terstruktur.
2. Memisahkan fungsi siswa, guru, dan administrator.
3. Memudahkan guru dalam mengelola materi pembelajaran.
4. Memudahkan pembuatan dan pengelolaan kuis.
5. Menyimpan hasil pembelajaran siswa secara terstruktur.
6. Mengurangi pekerjaan berulang melalui Material Bank dan Quiz Bank.
7. Menjadi project pembelajaran untuk memahami pengembangan aplikasi web menggunakan Python Flask.

---

## 🚧 Development Status

Tenebris-Class masih dalam tahap **development**.

Fitur utama yang telah tersedia meliputi:

* [x] User authentication
* [x] Student dashboard
* [x] Teacher dashboard
* [x] Admin user management
* [x] Subject management
* [x] Meeting management
* [x] Learning material management
* [x] File upload
* [x] Quiz system
* [x] Multiple-choice questions
* [x] Essay questions
* [x] Quiz results
* [x] Essay grading
* [x] Material Bank
* [x] Quiz Bank
* [x] Parser system
* [x] Automated tests

Pengembangan berikutnya dapat mencakup peningkatan UI/UX, penguatan sistem keamanan, pengelolaan database yang lebih baik, serta penyempurnaan sistem pembelajaran.

---

## 📌 Notes

Project ini dibuat sebagai project pembelajaran dan pengembangan aplikasi LMS.

Karena masih dalam tahap pengembangan, beberapa fitur dan implementasi dapat berubah pada versi berikutnya.

---

## 👤 Author

**jeruk125**

GitHub:
https://github.com/jeruk125

---

## 📄 License

License belum ditentukan untuk repository ini.

Jika project nantinya akan didistribusikan sebagai open-source, tambahkan file `LICENSE` dan tentukan lisensi yang sesuai.
