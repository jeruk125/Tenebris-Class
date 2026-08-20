import unittest
from app import app, db
from models import User, Subject, Meeting, Material, Quiz, QuestionMCQ

class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_full_workflow(self):
        with app.app_context():
            from werkzeug.security import generate_password_hash
            # 1. Create Admin & Student (admin might already exist due to app initialization, let's create a new unique one for test)
            admin = User(username='testadmin', password_hash=generate_password_hash('admin123'), role='admin')
            student = User(username='student1', password_hash=generate_password_hash('pass123'), role='siswa')
            db.session.add(admin)
            db.session.add(student)
            db.session.commit()

            admin_id = admin.id
            student_id = student.id

        # 2. Login as admin
        response = self.client.post('/admin_login', data=dict(username='testadmin', password='admin123'), follow_redirects=True)
        self.assertIn(b'Dashboard Guru', response.data)

        # 3. Create Subject
        response = self.client.post('/subject/create', data=dict(nama='Matematika Dasar'), follow_redirects=True)
        self.assertIn(b'Matematika Dasar', response.data)

        with app.app_context():
            subject = Subject.query.first()
            subject_id = subject.id

        # 4. Enroll Student
        response = self.client.post(f'/subject/{subject_id}/manage_students', data=dict(action='add', student_id=student_id), follow_redirects=True)

        # 5. Create Meeting
        response = self.client.post(f'/subject/{subject_id}/meeting/create', data=dict(judul='Pertemuan 1'), follow_redirects=True)

        with app.app_context():
            meeting = Meeting.query.first()
            meeting_id = meeting.id

        # 6. Create Quiz
        quiz_data = {
            'judul': 'Quiz 1',
            'tipe': 'pilihan_ganda',
            'teks_mentah': "SOAL 1\n1+1=?\nA. 1\nB. 2\nC. 3\nD. 4\nJAWABAN: B"
        }
        response = self.client.post(f'/meeting/{meeting_id}/quiz/create', data=quiz_data, follow_redirects=True)

        with app.app_context():
            quiz = Quiz.query.first()
            quiz_id = quiz.id
            question = QuestionMCQ.query.first()
            q_id = question.id

        # 7. Logout Admin
        self.client.get('/logout', follow_redirects=True)

        # 8. Login as Student
        response = self.client.post('/login', data=dict(username='student1', password='pass123'), follow_redirects=True)
        self.assertIn(b'Matematika Dasar', response.data)

        # 9. Take Quiz
        quiz_submit_data = {f'q_{q_id}': 'B'}
        response = self.client.post(f'/student/quiz/{quiz_id}', data=quiz_submit_data, follow_redirects=True)
        self.assertIn(b'100', response.data) # Check for score 100

if __name__ == '__main__':
    unittest.main()
