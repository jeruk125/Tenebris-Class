import unittest
from parsers import parse_material, parse_quiz_mcq, parse_quiz_text

class TestParsers(unittest.TestCase):
    def test_parse_material(self):
        raw_text = """JUDUL: Pengenalan Aljabar Dasar
TUJUAN: Siswa mampu memahami konsep variabel dan persamaan sederhana
MATERI: Aljabar adalah cabang matematika yang menggunakan simbol/huruf untuk mewakili angka...
CONTOH: 2x + 3 = 7, maka x = 2"""
        html = parse_material(raw_text)
        self.assertIn('<h2 class="material-judul">Pengenalan Aljabar Dasar</h2>', html)
        self.assertIn('<div class="material-tujuan"><strong>Tujuan:</strong><br>Siswa mampu memahami konsep variabel dan persamaan sederhana</div>', html)
        self.assertIn('Aljabar adalah cabang matematika', html)
        self.assertIn('<div class="material-contoh"><strong>Contoh:</strong><br>2x + 3 = 7, maka x = 2</div>', html)

    def test_parse_quiz_mcq(self):
        raw_text = """SOAL 1
Apa ibu kota Indonesia?
A. Bandung
B. Jakarta
C. Surabaya
D. Medan
JAWABAN: B
SOAL 2
Planet tempat kita tinggal adalah?
A. Mars
B. Venus
C. Bumi
D. Jupiter
JAWABAN: C"""
        questions = parse_quiz_mcq(raw_text)
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0]['pertanyaan'], 'Apa ibu kota Indonesia?')
        self.assertEqual(questions[0]['opsi_b'], 'Jakarta')
        self.assertEqual(questions[0]['jawaban_benar'], 'B')

        self.assertEqual(questions[1]['pertanyaan'], 'Planet tempat kita tinggal adalah?')
        self.assertEqual(questions[1]['jawaban_benar'], 'C')

    def test_parse_quiz_text(self):
        raw_text = """SOAL 1
Jelaskan proses fotosintesis!
SOAL 2
Sebutkan 3 ciri makhluk hidup."""
        questions = parse_quiz_text(raw_text)
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0]['pertanyaan'], 'Jelaskan proses fotosintesis!')
        self.assertEqual(questions[1]['pertanyaan'], 'Sebutkan 3 ciri makhluk hidup.')

if __name__ == '__main__':
    unittest.main()
