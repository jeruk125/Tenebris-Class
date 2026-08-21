from flask import Flask
from extensions import db, login_manager
from models import User
from werkzeug.security import generate_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_for_this_app')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp4'}

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import Subject, Meeting, Material, Quiz, QuestionMCQ, QuestionText, QuizResult

from werkzeug.utils import secure_filename
from markupsafe import Markup, escape

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.template_filter('nl2br')
def nl2br_filter(s):
    if not s:
        return ""
    return Markup('<br>\n'.join(escape(s).splitlines()))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'siswa':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('teacher_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, role='siswa').first()
        from werkzeug.security import check_password_hash
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('student_dashboard'))
        flash('Username atau password salah.', 'error')
    return render_template('login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        from werkzeug.security import check_password_hash
        if user and user.role in ['admin', 'guru'] and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('teacher_dashboard'))
        flash('Username atau password salah, atau Anda tidak memiliki akses ke portal ini.', 'error')
    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            flash('Password tidak cocok.', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username sudah digunakan.', 'error')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw, role='siswa')
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash('Registrasi berhasil! Selamat datang.', 'success')
        return redirect(url_for('student_dashboard'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard/siswa')
@login_required
def student_dashboard():
    if current_user.role != 'siswa':
        return redirect(url_for('index'))
    subjects = current_user.enrolled_subjects
    return render_template('student_dashboard.html', subjects=subjects)

@app.route('/student/subject/<int:subject_id>')
@login_required
def student_subject(subject_id):
    if current_user.role != 'siswa':
        return redirect(url_for('index'))
    subject = Subject.query.get_or_404(subject_id)
    if subject not in current_user.enrolled_subjects:
        flash('Anda tidak terdaftar di subjek ini.', 'error')
        return redirect(url_for('student_dashboard'))

    meetings = Meeting.query.filter_by(subjek_id=subject.id).order_by(Meeting.urutan).all()
    return render_template('student_subject.html', subject=subject, meetings=meetings)

@app.route('/student/material/<int:material_id>')
@login_required
def student_material(material_id):
    if current_user.role != 'siswa':
        return redirect(url_for('index'))
    material = Material.query.get_or_404(material_id)
    meeting = Meeting.query.get(material.pertemuan_id)
    subject = Subject.query.get(meeting.subjek_id)

    if subject not in current_user.enrolled_subjects:
        return redirect(url_for('student_dashboard'))

    parsed_content = parse_material(material.teks_mentah)
    return render_template('student_material.html', material=material, parsed_content=parsed_content, meeting=meeting)

@app.route('/student/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def student_quiz(quiz_id):
    if current_user.role != 'siswa':
        return redirect(url_for('index'))
    quiz = Quiz.query.get_or_404(quiz_id)
    meeting = Meeting.query.get(quiz.pertemuan_id)
    subject = Subject.query.get(meeting.subjek_id)

    if subject not in current_user.enrolled_subjects:
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        detail = {}
        if quiz.tipe == 'pilihan_ganda':
            benar = 0
            total = len(quiz.mcq_questions)
            for q in quiz.mcq_questions:
                jawaban_siswa = request.form.get(f'q_{q.id}')
                is_correct = (jawaban_siswa == q.jawaban_benar)
                if is_correct:
                    benar += 1
                detail[str(q.id)] = {
                    'pertanyaan': q.pertanyaan,
                    'jawaban_siswa': jawaban_siswa,
                    'jawaban_benar': q.jawaban_benar,
                    'is_correct': is_correct,
                    'opsi_a': q.opsi_a, 'opsi_b': q.opsi_b, 'opsi_c': q.opsi_c, 'opsi_d': q.opsi_d
                }
            skor = (benar / total * 100) if total > 0 else 0
        else:
            skor = None
            for q in quiz.text_questions:
                jawaban_siswa = request.form.get(f'q_{q.id}')
                detail[str(q.id)] = {
                    'pertanyaan': q.pertanyaan,
                    'jawaban_siswa': jawaban_siswa
                }

        result = QuizResult(siswa_id=current_user.id, quiz_id=quiz.id, skor=skor)
        result.detail = detail
        db.session.add(result)
        db.session.commit()

        flash('Quiz selesai dikerjakan.', 'success')
        return redirect(url_for('quiz_result_detail', result_id=result.id))

    # Get previous attempts
    attempts = QuizResult.query.filter_by(siswa_id=current_user.id, quiz_id=quiz.id).order_by(QuizResult.waktu_pengerjaan.desc()).all()

    return render_template('student_quiz.html', quiz=quiz, meeting=meeting, attempts=attempts)

@app.route('/student/quiz/result/<int:result_id>')
@login_required
def quiz_result_detail(result_id):
    if current_user.role != 'siswa':
        return redirect(url_for('index'))
    result = QuizResult.query.get_or_404(result_id)
    if result.siswa_id != current_user.id:
        return redirect(url_for('index'))
    quiz = Quiz.query.get(result.quiz_id)
    meeting = Meeting.query.get(quiz.pertemuan_id)

    return render_template('quiz_result.html', result=result, quiz=quiz, meeting=meeting)

@app.route('/dashboard/guru')
@login_required
def teacher_dashboard():
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    subjects = Subject.query.all()
    all_students = User.query.filter_by(role='siswa').all() if current_user.role == 'guru' else []
    return render_template('teacher_dashboard.html', subjects=subjects, all_students=all_students)

@app.route('/subject/create', methods=['POST'])
@login_required
def create_subject():
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    nama = request.form.get('nama')
    new_subject = Subject(nama=nama, dibuat_oleh=current_user.id)
    db.session.add(new_subject)
    db.session.commit()
    flash('Subjek berhasil ditambahkan.', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/subject/edit/<int:subject_id>', methods=['POST'])
@login_required
def edit_subject(subject_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    subject = Subject.query.get_or_404(subject_id)
    nama = request.form.get('nama')
    if nama:
        subject.nama = nama
        db.session.commit()
        flash('Subjek berhasil diperbarui.', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/subject/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subjek berhasil dihapus.', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/subject/<int:subject_id>')
@login_required
def teacher_subject_detail(subject_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    subject = Subject.query.get_or_404(subject_id)
    meetings = Meeting.query.filter_by(subjek_id=subject.id).order_by(Meeting.urutan).all()
    return render_template('teacher_subject.html', subject=subject, meetings=meetings)

@app.route('/subject/<int:subject_id>/manage_students', methods=['GET', 'POST'])
@login_required
def manage_students(subject_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    subject = Subject.query.get_or_404(subject_id)

    if request.method == 'POST':
        action = request.form.get('action')
        student_id = request.form.get('student_id')
        student = User.query.get(student_id)

        if action == 'add' and student:
            if student not in subject.students:
                subject.students.append(student)
                db.session.commit()
                flash(f'Siswa {student.username} ditambahkan ke subjek.', 'success')
        elif action == 'remove' and student:
            if student in subject.students:
                subject.students.remove(student)
                db.session.commit()
                flash(f'Siswa {student.username} dikeluarkan dari subjek.', 'success')
        return redirect(url_for('manage_students', subject_id=subject.id))

    all_students = User.query.filter_by(role='siswa').all()
    enrolled_students = subject.students.all()
    unenrolled_students = [s for s in all_students if s not in enrolled_students]

    return render_template('manage_students.html', subject=subject, enrolled=enrolled_students, unenrolled=unenrolled_students)

@app.route('/subject/<int:subject_id>/meeting/create', methods=['POST'])
@login_required
def create_meeting(subject_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    judul = request.form.get('judul')

    # Auto increment urutan
    last_meeting = Meeting.query.filter_by(subjek_id=subject_id).order_by(Meeting.urutan.desc()).first()
    urutan = last_meeting.urutan + 1 if last_meeting else 1

    new_meeting = Meeting(subjek_id=subject_id, judul=judul, urutan=urutan)
    db.session.add(new_meeting)
    db.session.commit()
    flash('Pertemuan berhasil ditambahkan.', 'success')
    return redirect(url_for('teacher_subject_detail', subject_id=subject_id))

@app.route('/meeting/edit/<int:meeting_id>', methods=['POST'])
@login_required
def edit_meeting(meeting_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    meeting = Meeting.query.get_or_404(meeting_id)
    judul = request.form.get('judul')
    if judul:
        meeting.judul = judul
        db.session.commit()
        flash('Pertemuan berhasil diperbarui.', 'success')
    return redirect(url_for('teacher_subject_detail', subject_id=meeting.subjek_id))

@app.route('/meeting/delete/<int:meeting_id>', methods=['POST'])
@login_required
def delete_meeting(meeting_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    meeting = Meeting.query.get_or_404(meeting_id)
    subject_id = meeting.subjek_id
    db.session.delete(meeting)
    db.session.commit()
    flash('Pertemuan berhasil dihapus.', 'success')
    return redirect(url_for('teacher_subject_detail', subject_id=subject_id))

from parsers import parse_material, parse_quiz_mcq, parse_quiz_text

import uuid
from models import MaterialFile
from flask import send_from_directory

@app.route('/meeting/<int:meeting_id>/material/create', methods=['GET', 'POST'])
@login_required
def create_material(meeting_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    meeting = Meeting.query.get_or_404(meeting_id)

    if request.method == 'POST':
        judul = request.form.get('judul')
        teks_mentah = request.form.get('teks_mentah')

        new_material = Material(
            pertemuan_id=meeting.id,
            judul=judul,
            teks_mentah=teks_mentah,
            dibuat_oleh=current_user.id
        )
        db.session.add(new_material)
        db.session.flush() # get material id

        files = request.files.getlist('files')
        for file in files:
            if file and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
                new_filename = f"{uuid.uuid4().hex}_{original_filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                file.save(file_path)

                mat_file = MaterialFile(
                    material_id=new_material.id,
                    filename=new_filename,
                    original_filename=original_filename
                )
                db.session.add(mat_file)

        db.session.commit()
        flash('Materi berhasil ditambahkan.', 'success')
        return redirect(url_for('teacher_subject_detail', subject_id=meeting.subjek_id))

    return render_template('material_form.html', meeting=meeting, action='Create')

@app.route('/material/edit/<int:material_id>', methods=['GET', 'POST'])
@login_required
def edit_material(material_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    material = Material.query.get_or_404(material_id)
    meeting = Meeting.query.get(material.pertemuan_id)

    if request.method == 'POST':
        material.judul = request.form.get('judul')
        material.teks_mentah = request.form.get('teks_mentah')

        files = request.files.getlist('files')
        for file in files:
            if file and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
                new_filename = f"{uuid.uuid4().hex}_{original_filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                file.save(file_path)

                mat_file = MaterialFile(
                    material_id=material.id,
                    filename=new_filename,
                    original_filename=original_filename
                )
                db.session.add(mat_file)

        db.session.commit()
        flash('Materi berhasil diperbarui.', 'success')
        return redirect(url_for('teacher_subject_detail', subject_id=meeting.subjek_id))

    return render_template('material_form.html', meeting=meeting, material=material, action='Edit')

@app.route('/material/file/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_material_file(file_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    mat_file = MaterialFile.query.get_or_404(file_id)
    material_id = mat_file.material_id

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], mat_file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(mat_file)
    db.session.commit()
    flash('File berhasil dihapus.', 'success')
    return redirect(url_for('edit_material', material_id=material_id))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/material/delete/<int:material_id>', methods=['POST'])
@login_required
def delete_material(material_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    material = Material.query.get_or_404(material_id)
    meeting = Meeting.query.get(material.pertemuan_id)

    # clean up physical files
    for mat_file in material.files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], mat_file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(material)
    db.session.commit()
    flash('Materi berhasil dihapus.', 'success')
    return redirect(url_for('teacher_subject_detail', subject_id=meeting.subjek_id))


from flask import jsonify

@app.route('/api/parse_quiz_raw', methods=['POST'])
@login_required
def parse_quiz_raw():
    if current_user.role not in ['admin', 'guru']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data or 'teks_mentah' not in data or 'tipe' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    tipe = data['tipe']
    teks = data['teks_mentah']

    if tipe == 'pilihan_ganda':
        questions = parse_quiz_mcq(teks)
    elif tipe == 'teks':
        questions = parse_quiz_text(teks)
    else:
        return jsonify({'error': 'Unknown type'}), 400

    return jsonify({'questions': questions})

import json

def reconstruct_quiz_raw_text(tipe, questions_data):
    """Reconstructs the original raw text block format from a list of question dicts"""
    raw_lines = []
    for i, q in enumerate(questions_data, 1):
        raw_lines.append(f"SOAL {i}")
        raw_lines.append(q.get('pertanyaan', ''))
        if tipe == 'pilihan_ganda':
            raw_lines.append(f"A. {q.get('opsi_a', '')}")
            raw_lines.append(f"B. {q.get('opsi_b', '')}")
            raw_lines.append(f"C. {q.get('opsi_c', '')}")
            raw_lines.append(f"D. {q.get('opsi_d', '')}")
            raw_lines.append(f"JAWABAN: {q.get('jawaban_benar', 'A')}")
        # For essay, we just need the question.
    return '\n'.join(raw_lines)

@app.route('/meeting/<int:meeting_id>/quiz/create', methods=['GET', 'POST'])
@login_required
def create_quiz(meeting_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    meeting = Meeting.query.get_or_404(meeting_id)

    if request.method == 'POST':
        judul = request.form.get('judul')
        tipe = request.form.get('tipe')
        questions_data_str = request.form.get('questions_data')

        try:
            questions_data = json.loads(questions_data_str)
        except:
            questions_data = []

        teks_mentah = reconstruct_quiz_raw_text(tipe, questions_data)

        new_quiz = Quiz(
            pertemuan_id=meeting.id,
            judul=judul,
            tipe=tipe,
            teks_mentah=teks_mentah,
            dibuat_oleh=current_user.id
        )
        db.session.add(new_quiz)
        db.session.flush() # get quiz id

        # Create questions based on structured data
        if tipe == 'pilihan_ganda':
            for q_data in questions_data:
                q = QuestionMCQ(
                    quiz_id=new_quiz.id,
                    pertanyaan=q_data.get('pertanyaan',''),
                    opsi_a=q_data.get('opsi_a',''), opsi_b=q_data.get('opsi_b',''),
                    opsi_c=q_data.get('opsi_c',''), opsi_d=q_data.get('opsi_d',''),
                    jawaban_benar=q_data.get('jawaban_benar','A')
                )
                db.session.add(q)
        elif tipe == 'teks':
            for q_data in questions_data:
                q = QuestionText(
                    quiz_id=new_quiz.id,
                    pertanyaan=q_data.get('pertanyaan',''),
                    jawaban_referensi=q_data.get('jawaban_referensi','')
                )
                db.session.add(q)

        db.session.commit()
        flash('Quiz berhasil ditambahkan.', 'success')
        return redirect(url_for('teacher_subject_detail', subject_id=meeting.subjek_id))

    return render_template('quiz_form.html', meeting=meeting, action='Create')

@app.route('/quiz/edit/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    quiz = Quiz.query.get_or_404(quiz_id)
    meeting = Meeting.query.get(quiz.pertemuan_id)

    if request.method == 'POST':
        quiz.judul = request.form.get('judul')
        # We don't allow changing type during edit for simplicity, or we can just drop old questions if they do.
        # But UI allows it (changing type drops questions via JS), so we handle it:
        new_tipe = request.form.get('tipe')
        questions_data_str = request.form.get('questions_data')

        try:
            questions_data = json.loads(questions_data_str)
        except:
            questions_data = []

        teks_mentah = reconstruct_quiz_raw_text(new_tipe, questions_data)

        quiz.tipe = new_tipe
        quiz.teks_mentah = teks_mentah

        # Delete old questions
        if quiz.tipe == 'pilihan_ganda' or new_tipe != quiz.tipe:
            for q in quiz.mcq_questions: db.session.delete(q)
        if quiz.tipe == 'teks' or new_tipe != quiz.tipe:
            for q in quiz.text_questions: db.session.delete(q)

        db.session.flush()

        # Insert new questions
        if new_tipe == 'pilihan_ganda':
            for q_data in questions_data:
                q = QuestionMCQ(
                    quiz_id=quiz.id,
                    pertanyaan=q_data.get('pertanyaan',''),
                    opsi_a=q_data.get('opsi_a',''), opsi_b=q_data.get('opsi_b',''),
                    opsi_c=q_data.get('opsi_c',''), opsi_d=q_data.get('opsi_d',''),
                    jawaban_benar=q_data.get('jawaban_benar','A')
                )
                db.session.add(q)
        elif new_tipe == 'teks':
            for q_data in questions_data:
                q = QuestionText(
                    quiz_id=quiz.id,
                    pertanyaan=q_data.get('pertanyaan',''),
                    jawaban_referensi=q_data.get('jawaban_referensi','')
                )
                db.session.add(q)

        db.session.commit()
        flash('Quiz berhasil diperbarui.', 'success')
        return redirect(url_for('teacher_subject_detail', subject_id=meeting.subjek_id))

    return render_template('quiz_form.html', meeting=meeting, quiz=quiz, action='Edit')

@app.route('/quiz/delete/<int:quiz_id>', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    quiz = Quiz.query.get_or_404(quiz_id)
    meeting = Meeting.query.get(quiz.pertemuan_id)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz berhasil dihapus.', 'success')
    return redirect(url_for('teacher_subject_detail', subject_id=meeting.subjek_id))


@app.route('/quiz/<int:quiz_id>/results')
@login_required
def view_quiz_results(quiz_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    quiz = Quiz.query.get_or_404(quiz_id)
    results = QuizResult.query.filter_by(quiz_id=quiz.id).order_by(QuizResult.waktu_pengerjaan.desc()).all()
    # Eager load users for display
    for r in results:
        r.student = User.query.get(r.siswa_id)
    return render_template('quiz_results_admin.html', quiz=quiz, results=results)

@app.route('/quiz/result/<int:result_id>/detail')
@login_required
def admin_quiz_result_detail(result_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    result = QuizResult.query.get_or_404(result_id)
    quiz = Quiz.query.get(result.quiz_id)
    student = User.query.get(result.siswa_id)
    return render_template('admin_quiz_result_detail.html', result=result, quiz=quiz, student=student)

@app.route('/quiz/result/<int:result_id>/grade', methods=['POST'])
@login_required
def grade_quiz_essay(result_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))

    result = QuizResult.query.get_or_404(result_id)

    total_score = request.form.get('total_score')
    if total_score is not None:
        try:
            result.skor = float(total_score)

            # Optionally update individual details with points
            current_detail = dict(result.detail) # force new object to ensure JSON mutation tracked
            for q_id in current_detail:
                point_val = request.form.get(f'point_{q_id}')
                if point_val:
                    current_detail[q_id]['poin'] = float(point_val)

            # Set via the setter which does json.dumps
            result.detail = current_detail

            # mark modified for SQLAlchemy
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(result, "detail_jawaban")

            db.session.commit()
            flash('Nilai berhasil disimpan.', 'success')
        except ValueError:
            flash('Format nilai tidak valid.', 'error')

    return redirect(url_for('admin_quiz_result_detail', result_id=result.id))

@app.route('/quiz/result/delete/<int:result_id>', methods=['POST'])
@login_required
def delete_quiz_result(result_id):
    if current_user.role not in ['admin', 'guru']:
        return redirect(url_for('index'))
    result = QuizResult.query.get_or_404(result_id)
    quiz_id = result.quiz_id
    db.session.delete(result)
    db.session.commit()
    flash('Hasil quiz berhasil dihapus.', 'success')
    return redirect(url_for('view_quiz_results', quiz_id=quiz_id))


@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Akses ditolak.', 'error')
        return redirect(url_for('index'))
    teachers = User.query.filter_by(role='guru').all()
    students = User.query.filter_by(role='siswa').all()
    return render_template('admin_users.html', teachers=teachers, students=students)

@app.route('/admin/teacher/add', methods=['POST'])
@login_required
def add_teacher():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    username = request.form.get('username')
    password = request.form.get('password')

    if User.query.filter_by(username=username).first():
        flash('Username sudah digunakan.', 'error')
        return redirect(url_for('admin_users'))

    hashed_pw = generate_password_hash(password)
    new_teacher = User(username=username, password_hash=hashed_pw, role='guru')
    db.session.add(new_teacher)
    db.session.commit()
    flash('Akun guru berhasil ditambahkan.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.role == 'admin':
        if user.role == 'admin':
            flash('Tidak dapat menghapus admin.', 'error')
        else:
            db.session.delete(user)
            db.session.commit()
            flash('Akun berhasil dihapus.', 'success')
    elif current_user.role == 'guru' and user.role == 'siswa':
        db.session.delete(user)
        db.session.commit()
        flash('Akun siswa berhasil dihapus.', 'success')
    else:
        flash('Akses ditolak.', 'error')

    return redirect(request.referrer or url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        from werkzeug.security import check_password_hash
        if not check_password_hash(current_user.password_hash, old_password):
            flash('Password lama salah.', 'error')
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash('Password baru tidak cocok.', 'error')
            return redirect(url_for('change_password'))

        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Password berhasil diubah.', 'success')
        return redirect(url_for('index'))

    return render_template('change_password.html')

def create_admin():
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            hashed_pw = generate_password_hash('admin123')
            admin = User(username='admin', password_hash=hashed_pw, role='admin')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created (admin/admin123). Please change password after first login.")

if __name__ == '__main__':
    create_admin()
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    )