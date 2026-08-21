from flask_login import UserMixin
from extensions import db
import json

# Association table for students and subjects
student_subjects = db.Table('student_subjects',
    db.Column('student_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subject.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'guru', 'siswa'

    # Relationships
    subjects_created = db.relationship('Subject', backref='creator', lazy=True)
    enrolled_subjects = db.relationship('Subject', secondary=student_subjects, backref=db.backref('students', lazy='dynamic'))

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(200), nullable=False)
    dibuat_oleh = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    meetings = db.relationship('Meeting', backref='subject', cascade="all, delete-orphan", lazy=True)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subjek_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    judul = db.Column(db.String(200), nullable=False)
    urutan = db.Column(db.Integer, nullable=False)

    materials = db.relationship('Material', backref='meeting', cascade="all, delete-orphan", lazy=True)
    quizzes = db.relationship('Quiz', backref='meeting', cascade="all, delete-orphan", lazy=True)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pertemuan_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    judul = db.Column(db.String(200), nullable=False)
    teks_mentah = db.Column(db.Text, nullable=False)
    dibuat_oleh = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    files = db.relationship('MaterialFile', backref='material', cascade="all, delete-orphan", lazy=True)

class MaterialFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pertemuan_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    judul = db.Column(db.String(200), nullable=False)
    tipe = db.Column(db.String(20), nullable=False) # 'pilihan_ganda' or 'teks'
    teks_mentah = db.Column(db.Text, nullable=False)
    dibuat_oleh = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    mcq_questions = db.relationship('QuestionMCQ', backref='quiz', cascade="all, delete-orphan", lazy=True)
    text_questions = db.relationship('QuestionText', backref='quiz', cascade="all, delete-orphan", lazy=True)
    results = db.relationship('QuizResult', backref='quiz', cascade="all, delete-orphan", lazy=True)

class QuestionMCQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    pertanyaan = db.Column(db.Text, nullable=False)
    opsi_a = db.Column(db.String(500), nullable=False)
    opsi_b = db.Column(db.String(500), nullable=False)
    opsi_c = db.Column(db.String(500), nullable=False)
    opsi_d = db.Column(db.String(500), nullable=False)
    jawaban_benar = db.Column(db.String(1), nullable=False) # A, B, C, or D

class QuestionText(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    pertanyaan = db.Column(db.Text, nullable=False)
    jawaban_referensi = db.Column(db.Text, nullable=True)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    siswa_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    waktu_pengerjaan = db.Column(db.DateTime, default=db.func.current_timestamp())
    skor = db.Column(db.Float, nullable=True) # None for essay quizzes
    detail_jawaban = db.Column(db.Text, nullable=False) # Stored as JSON string

    @property
    def detail(self):
        return json.loads(self.detail_jawaban) if self.detail_jawaban else {}

    @detail.setter
    def detail(self, value):
        self.detail_jawaban = json.dumps(value)
