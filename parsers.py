import re

def parse_material(raw_text):
    """
    Parses raw text with labels (e.g., JUDUL:, TUJUAN:, MATERI:, CONTOH:)
    into structured HTML.
    """
    lines = raw_text.split('\n')
    html_output = []

    current_label = None
    current_content = []

    def process_block(label, content):
        if not content: return ""
        text = "<br>".join(content)
        if label == 'JUDUL':
            return f'<h2 class="material-judul">{text}</h2>'
        elif label == 'TUJUAN':
            return f'<div class="material-tujuan"><strong>Tujuan:</strong><br>{text}</div>'
        elif label == 'MATERI':
            return f'<div class="material-teks">{text}</div>'
        elif label == 'CONTOH':
            return f'<div class="material-contoh"><strong>Contoh:</strong><br>{text}</div>'
        else:
            # Fallback for unknown labels (can be expanded later)
            return f'<div class="material-section material-{label.lower()}"><strong>{label}:</strong><br>{text}</div>'

    for line in lines:
        line_stripped = line.strip()
        # Look for a label pattern: ALL CAPS followed by a colon
        match = re.match(r'^([A-Z_]+):(.*)$', line_stripped)
        if match:
            if current_label:
                html_output.append(process_block(current_label, current_content))
            current_label = match.group(1)
            content_part = match.group(2).strip()
            current_content = [content_part] if content_part else []
        else:
            if current_label:
                current_content.append(line_stripped)
            else:
                # If there's text before any label, wrap it in a generic div
                if line_stripped:
                    html_output.append(f'<div>{line_stripped}</div>')

    if current_label:
        html_output.append(process_block(current_label, current_content))

    return "\n".join(html_output)


def parse_quiz_mcq(raw_text):
    """
    Parses MCQ quiz text into a list of dictionaries.
    Expected format:
    SOAL 1
    Pertanyaan...
    A. Opsi 1
    B. Opsi 2
    C. Opsi 3
    D. Opsi 4
    JAWABAN: B
    """
    questions = []
    blocks = re.split(r'^SOAL\s+\d+\s*$', raw_text, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split('\n')
        question_text = []
        options = {}
        correct_answer = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            opt_match = re.match(r'^([A-Z])\.\s*(.*)$', line)
            ans_match = re.match(r'^JAWABAN:\s*([A-Z])$', line, re.IGNORECASE)

            if ans_match:
                correct_answer = ans_match.group(1).upper()
            elif opt_match:
                options[opt_match.group(1)] = opt_match.group(2)
            else:
                question_text.append(line)
            i += 1

        if question_text and options and correct_answer:
            questions.append({
                'pertanyaan': '\n'.join(question_text),
                'opsi_a': options.get('A', ''),
                'opsi_b': options.get('B', ''),
                'opsi_c': options.get('C', ''),
                'opsi_d': options.get('D', ''),
                'jawaban_benar': correct_answer
            })

    return questions

def parse_quiz_text(raw_text):
    """
    Parses Essay quiz text into a list of dictionaries.
    Expected format:
    SOAL 1
    Pertanyaan...
    """
    questions = []
    blocks = re.split(r'^SOAL\s+\d+\s*$', raw_text, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        questions.append({
            'pertanyaan': block,
            'jawaban_referensi': None # Can be expanded later
        })

    return questions
