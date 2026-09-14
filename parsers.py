import re

class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value}, line={self.line})"

class Tokenizer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.tokens = []

    def tokenize(self):
        lines = self.text.split('\n')

        for i, line in enumerate(lines):
            self.line = i + 1
            # We need to find tags like [TAG] and [/TAG]
            # Since tags are usually on their own lines or wrapping text, we use regex to find all tags
            # A simple way is to tokenize line by line, splitting by tags

            # Find all tag matches in the line
            pattern = re.compile(r'(\[/?(?:[A-Z0-9_]+\s?[A-Z0-9_]*)\])')
            parts = pattern.split(line)

            for part in parts:
                if not part:
                    continue
                if part.startswith('[/') and part.endswith(']'):
                    tag_name = part[2:-1].strip()
                    self.tokens.append(Token('CLOSE_TAG', tag_name, self.line))
                elif part.startswith('[') and part.endswith(']'):
                    tag_name = part[1:-1].strip()
                    self.tokens.append(Token('OPEN_TAG', tag_name, self.line))
                else:
                    # It's text. Let's only add if it's not purely empty when stripped,
                    # OR if we want to preserve whitespace, we should add it all.
                    # Wait, preserving paragraph breaks is important. We will add text tokens verbatim.
                    self.tokens.append(Token('TEXT', part, self.line))

            # Add a newline token to preserve line breaks for paragraphs, unless it's the last line
            if i < len(lines) - 1:
                self.tokens.append(Token('NEWLINE', '\n', self.line))

        # Cleanup: merge consecutive TEXT and NEWLINE tokens into single TEXT tokens to make AST building easier
        cleaned_tokens = []
        current_text = []
        current_line = 1

        for token in self.tokens:
            if token.type in ('TEXT', 'NEWLINE'):
                current_text.append(token.value)
                current_line = token.line
            else:
                if current_text:
                    merged_text = ''.join(current_text)
                    if merged_text.strip(): # keep only if it has some non-whitespace OR if we strictly want all? We must keep paragraph structure. Let's keep all and trim later.
                        cleaned_tokens.append(Token('TEXT', merged_text, current_line))
                    current_text = []
                cleaned_tokens.append(token)

        if current_text:
            merged_text = ''.join(current_text)
            if merged_text.strip():
                cleaned_tokens.append(Token('TEXT', merged_text, current_line))

        return cleaned_tokens


class BlockNode:
    def __init__(self, tag, line):
        self.tag = tag
        self.line = line
        self.children = []

    def __repr__(self):
        return f"BlockNode({self.tag}, children={len(self.children)})"

class TextNode:
    def __init__(self, text, line):
        self.text = text
        self.line = line

    def __repr__(self):
        return f"TextNode({repr(self.text)})"

class ASTBuilder:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def build(self):
        root = BlockNode('ROOT', 0)
        stack = [root]

        for token in self.tokens:
            if token.type == 'OPEN_TAG':
                node = BlockNode(token.value, token.line)
                stack[-1].children.append(node)
                stack.append(node)
            elif token.type == 'CLOSE_TAG':
                if len(stack) > 1:
                    if stack[-1].tag == token.value:
                        stack.pop()
                    else:
                        self.errors.append({
                            'line': token.line,
                            'message': f"Mismatched closing tag. Expected [/{stack[-1].tag}], found [/{token.value}]."
                        })
                        # Heuristic recovery: just ignore the bad closing tag and keep the block open
                else:
                    self.errors.append({
                        'line': token.line,
                        'message': f"Unexpected closing tag [/{token.value}] without matching opening tag."
                    })
            elif token.type == 'TEXT':
                # Strip leading/trailing whitespace strictly for purely empty nodes, but keep inner newlines.
                # Actually, we should just append it.
                stack[-1].children.append(TextNode(token.value, token.line))

        if len(stack) > 1:
            for unclosed in reversed(stack[1:]):
                self.errors.append({
                    'line': unclosed.line,
                    'message': f"Missing closing tag for [{unclosed.tag}]."
                })

        return root, self.errors

# --- LEGACY PARSERS BELOW ---
def legacy_parse_material(raw_text):
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
            return f'<div class="material-section material-{label.lower()}"><strong>{label}:</strong><br>{text}</div>'

    for line in lines:
        line_stripped = line.strip()
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
                if line_stripped:
                    html_output.append(f'<div>{line_stripped}</div>')

    if current_label:
        html_output.append(process_block(current_label, current_content))

    return "\n".join(html_output)

def legacy_parse_quiz_mcq(raw_text):
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

def legacy_parse_quiz_text(raw_text):
    questions = []
    blocks = re.split(r'^SOAL\s+\d+\s*$', raw_text, flags=re.MULTILINE)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        questions.append({
            'pertanyaan': block,
            'jawaban_referensi': None
        })
    return questions

# Placeholder for new API functions
def parse_material(raw_text):
    return {"success": True, "content": legacy_parse_material(raw_text), "errors": []}

def parse_quiz_mcq(raw_text):
    return legacy_parse_quiz_mcq(raw_text)

def parse_quiz_text(raw_text):
    return legacy_parse_quiz_text(raw_text)


class MaterialRenderer:
    def __init__(self, root_node):
        self.root_node = root_node
        self.errors = []

    def render(self):
        # Find the main MATERIAL block
        material_nodes = [c for c in self.root_node.children if isinstance(c, BlockNode) and c.tag == 'MATERIAL']
        if not material_nodes:
            self.errors.append({"line": 1, "message": "Missing [MATERIAL] block."})
            return ""

        return self._render_node(material_nodes[0])

    def _render_node(self, node):
        from markupsafe import escape

        if isinstance(node, TextNode):
            # Safe HTML escape of text
            text = str(escape(node.text))

            # Simple conversion of double newlines to paragraphs
            parts = text.split('\n\n')
            html_parts = []
            for part in parts:
                part = part.strip()
                if part:
                    # Single newlines within a paragraph get <br>
                    part_with_br = part.replace('\n', '<br>')
                    html_parts.append(f'<p>{part_with_br}</p>')
            return '\n'.join(html_parts)

        if isinstance(node, BlockNode):
            inner_html = ""
            for child in node.children:
                inner_html += self._render_node(child)

            tag = node.tag

            if tag == 'MATERIAL':
                return f'<div class="tc-material">\n{inner_html}\n</div>'
            elif tag == 'TITLE':
                # Strip wrapping p tags if title is single line
                inner_html = self._strip_outer_p(inner_html)
                return f'<h1 class="tc-title">{inner_html}</h1>'
            elif tag == 'HEADING':
                inner_html = self._strip_outer_p(inner_html)
                return f'<h2 class="tc-heading">{inner_html}</h2>'
            elif tag == 'PARAGRAPH':
                return inner_html # TextNode already wraps in <p>
            elif tag == 'NOTE':
                return f'<div class="tc-note"><strong>Note:</strong><br>{inner_html}</div>'
            elif tag == 'WARNING':
                return f'<div class="tc-warning"><strong>Warning:</strong><br>{inner_html}</div>'
            elif tag == 'SUMMARY':
                return f'<div class="tc-summary"><strong>Summary:</strong><br>{inner_html}</div>'
            elif tag == 'EXAMPLE':
                return f'<div class="tc-example"><strong>Example:</strong><br>{inner_html}</div>'
            elif tag == 'OBJECTIVE':
                return f'<div class="tc-objective"><strong>Objective:</strong><br>{inner_html}</div>'
            elif tag == 'STEPS':
                return f'<div class="tc-steps">\n{inner_html}\n</div>'
            elif tag == 'STEP':
                inner_html = self._strip_outer_p(inner_html)
                return f'<div class="tc-step">{inner_html}</div>'
            elif tag == 'FORMULA':
                # Don't convert newlines to p tags for raw content blocks
                raw_text = self._get_raw_text(node).strip()
                safe_formula = escape(raw_text)
                return f'<pre class="tc-formula"><code>{safe_formula}</code></pre>'
            elif tag == 'CODE':
                raw_text = self._get_raw_text(node).strip()
                safe_code = escape(raw_text)
                return f'<pre class="tc-code"><code>{safe_code}</code></pre>'
            elif tag == 'DATASET' or tag == 'TABLE':
                raw_text = self._get_raw_text(node).strip()
                return self._render_table(raw_text)
            else:
                self.errors.append({"line": node.line, "message": f"Unknown tag: [{node.tag}]"})
                return inner_html

        return ""

    def _strip_outer_p(self, html):
        html = html.strip()
        if html.startswith('<p>') and html.endswith('</p>'):
            return html[3:-4]
        return html

    def _get_raw_text(self, node):
        text = ""
        for child in node.children:
            if isinstance(child, TextNode):
                text += child.text
            elif isinstance(child, BlockNode):
                text += self._get_raw_text(child)
        return text

    def _render_table(self, raw_text):
        from markupsafe import escape
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        if not lines:
            return ""

        html = ['<div class="tc-table-container">']
        html.append('<button type="button" class="tc-copy-btn" onclick="copyTableToExcel(this)">Copy Table</button>')
        html.append('<table class="tc-table">')

        for i, line in enumerate(lines):
            cells = [cell.strip() for cell in line.split('|')]
            if i == 0:
                html.append('  <thead>')
                html.append('    <tr>')
                for cell in cells:
                    html.append(f'      <th>{escape(cell)}</th>')
                html.append('    </tr>')
                html.append('  </thead>')
                html.append('  <tbody>')
            else:
                html.append('    <tr>')
                for cell in cells:
                    html.append(f'      <td>{escape(cell)}</td>')
                html.append('    </tr>')

        if len(lines) > 0:
            html.append('  </tbody>')
        html.append('</table>')
        html.append('</div>')

        return '\n'.join(html)


class QuizRenderer:
    def __init__(self, root_node, quiz_type):
        self.root_node = root_node
        self.quiz_type = quiz_type # 'pilihan_ganda' or 'teks'
        self.errors = []
        self.questions = []

    def render(self):
        quiz_nodes = [c for c in self.root_node.children if isinstance(c, BlockNode) and c.tag == 'QUIZ']
        if not quiz_nodes:
            self.errors.append({"line": 1, "message": "Missing [QUIZ] block."})
            return []

        quiz_node = quiz_nodes[0]

        # Verify type if specified
        type_nodes = [c for c in quiz_node.children if isinstance(c, BlockNode) and c.tag == 'TYPE']
        if type_nodes:
            declared_type = self._get_raw_text(type_nodes[0]).strip().lower()
            if declared_type != self.quiz_type and not (declared_type == 'essay' and self.quiz_type == 'teks'):
                 self.errors.append({"line": type_nodes[0].line, "message": f"Quiz type mismatch. Expected '{self.quiz_type}', found '{declared_type}'."})
                 return []

        # Parse questions
        question_nodes = [c for c in quiz_node.children if isinstance(c, BlockNode) and c.tag.startswith('QUESTION ')]

        for q_node in question_nodes:
            self._parse_question(q_node)

        return self.questions

    def _parse_question(self, node):
        q_text_node = self._find_first_child(node, 'QUESTION')
        if not q_text_node:
            self.errors.append({"line": node.line, "message": f"Missing [QUESTION] in [{node.tag}]."})
            return

        pertanyaan = self._get_raw_text(q_text_node).strip()

        if self.quiz_type == 'pilihan_ganda':
            options_node = self._find_first_child(node, 'OPTIONS')
            answer_node = self._find_first_child(node, 'ANSWER')

            if not options_node:
                self.errors.append({"line": node.line, "message": f"Missing [OPTIONS] in [{node.tag}]."})
                return
            if not answer_node:
                self.errors.append({"line": node.line, "message": f"Missing [ANSWER] in [{node.tag}]."})
                return

            opsi_a = opsi_b = opsi_c = opsi_d = ""
            options_text = self._get_raw_text(options_node).strip()
            lines = options_text.split('\n')

            import re
            for line in lines:
                line = line.strip()
                match = re.match(r'^([A-D])\.\s*(.*)$', line)
                if match:
                    opt = match.group(1).upper()
                    val = match.group(2)
                    if opt == 'A': opsi_a = val
                    elif opt == 'B': opsi_b = val
                    elif opt == 'C': opsi_c = val
                    elif opt == 'D': opsi_d = val

            jawaban_benar = self._get_raw_text(answer_node).strip().upper()
            if jawaban_benar not in ['A', 'B', 'C', 'D']:
                self.errors.append({"line": answer_node.line, "message": f"Invalid [ANSWER] '{jawaban_benar}' in [{node.tag}]. Must be A, B, C, or D."})

            self.questions.append({
                'pertanyaan': pertanyaan,
                'opsi_a': opsi_a,
                'opsi_b': opsi_b,
                'opsi_c': opsi_c,
                'opsi_d': opsi_d,
                'jawaban_benar': jawaban_benar
            })

        else: # essay
            answer_node = self._find_first_child(node, 'ANSWER')
            jawaban_referensi = self._get_raw_text(answer_node).strip() if answer_node else ""

            self.questions.append({
                'pertanyaan': pertanyaan,
                'jawaban_referensi': jawaban_referensi
            })

    def _find_first_child(self, node, tag):
        for child in node.children:
            if isinstance(child, BlockNode) and child.tag == tag:
                return child
        return None

    def _get_raw_text(self, node):
        text = ""
        for child in node.children:
            if isinstance(child, TextNode):
                text += child.text
            elif isinstance(child, BlockNode):
                text += self._get_raw_text(child)
        return text

def parse_material(raw_text):
    if '[MATERIAL]' in raw_text or '[EXERCISE]' in raw_text or '[PROJECT]' in raw_text:
        tokens = Tokenizer(raw_text).tokenize()
        ast, ast_errors = ASTBuilder(tokens).build()

        # If it's a project or exercise, we might want to render them generically if they are the root.
        # But our MaterialRenderer expects [MATERIAL]. Let's make it handle [EXERCISE] and [PROJECT] too.
        # We'll update the renderer logic slightly below.

        renderer = ExtendedMaterialRenderer(ast)
        html = renderer.render()
        errors = ast_errors + renderer.errors

        return {
            "success": len(errors) == 0,
            "content": html,
            "errors": errors
        }
    else:
        # Fallback to legacy parser
        html = legacy_parse_material(raw_text)
        return {
            "success": True,
            "content": html,
            "errors": []
        }

def parse_quiz_mcq(raw_text):
    if '[QUIZ]' in raw_text:
        tokens = Tokenizer(raw_text).tokenize()
        ast, ast_errors = ASTBuilder(tokens).build()

        renderer = QuizRenderer(ast, 'pilihan_ganda')
        questions = renderer.render()
        errors = ast_errors + renderer.errors

        # We need to adapt the signature if we want to return structured results.
        # For legacy compatibility in app.py which expects a list directly for import_quiz/parse_quiz_raw,
        # we will check if the user of parse_quiz_mcq expects a list or a dict.
        # However, the prompt specifically says "Change the return signature of all parsers to a structured dictionary".
        # Let's do that and update app.py later. Wait, for `parse_quiz_mcq`, if we change the return signature, we MUST update app.py immediately.
        # Let's keep the return as dict for the final integration, but app.py needs updating.
        return {
            "success": len(errors) == 0,
            "content": questions,
            "errors": errors
        }
    else:
        questions = legacy_parse_quiz_mcq(raw_text)
        return {
            "success": True,
            "content": questions,
            "errors": []
        }

def parse_quiz_text(raw_text):
    if '[QUIZ]' in raw_text:
        tokens = Tokenizer(raw_text).tokenize()
        ast, ast_errors = ASTBuilder(tokens).build()

        renderer = QuizRenderer(ast, 'teks')
        questions = renderer.render()
        errors = ast_errors + renderer.errors

        return {
            "success": len(errors) == 0,
            "content": questions,
            "errors": errors
        }
    else:
        questions = legacy_parse_quiz_text(raw_text)
        return {
            "success": True,
            "content": questions,
            "errors": []
        }

# To ensure the MaterialRenderer handles all required blocks for EXERCISE and PROJECT:
class ExtendedMaterialRenderer(MaterialRenderer):
    def render(self):
        # Allow ROOT to process multiple main blocks if needed, but typically there's one.
        # Find all main container blocks
        main_nodes = [c for c in self.root_node.children if isinstance(c, BlockNode) and c.tag in ('MATERIAL', 'EXERCISE', 'PROJECT')]
        if not main_nodes:
            self.errors.append({"line": 1, "message": "Missing main block [MATERIAL], [EXERCISE], or [PROJECT]."})
            return ""

        html_out = ""
        for node in main_nodes:
            html_out += self._render_node(node)
        return html_out

    def _render_node(self, node):
        from markupsafe import escape

        if isinstance(node, TextNode):
            text = str(escape(node.text))
            parts = text.split('\n\n')
            html_parts = []
            for part in parts:
                part = part.strip()
                if part:
                    part_with_br = part.replace('\n', '<br>')
                    html_parts.append(f'<p>{part_with_br}</p>')
            return '\n'.join(html_parts)

        if isinstance(node, BlockNode):
            inner_html = ""
            for child in node.children:
                inner_html += self._render_node(child)

            tag = node.tag

            # --- Base Blocks ---
            if tag == 'MATERIAL':
                return f'<div class="tc-material">\n{inner_html}\n</div>'
            elif tag == 'EXERCISE':
                return f'<div class="tc-exercise">\n{inner_html}\n</div>'
            elif tag == 'PROJECT':
                return f'<div class="tc-project">\n{inner_html}\n</div>'

            elif tag == 'TITLE':
                inner_html = self._strip_outer_p(inner_html)
                return f'<h1 class="tc-title">{inner_html}</h1>'
            elif tag == 'HEADING':
                inner_html = self._strip_outer_p(inner_html)
                return f'<h2 class="tc-heading">{inner_html}</h2>'
            elif tag == 'PARAGRAPH':
                return inner_html

            elif tag == 'NOTE':
                return f'<div class="tc-note"><strong>Note:</strong><br>{inner_html}</div>'
            elif tag == 'WARNING':
                return f'<div class="tc-warning"><strong>Warning:</strong><br>{inner_html}</div>'
            elif tag == 'SUMMARY':
                return f'<div class="tc-summary"><strong>Summary:</strong><br>{inner_html}</div>'
            elif tag == 'EXAMPLE':
                return f'<div class="tc-example"><strong>Example:</strong><br>{inner_html}</div>'
            elif tag == 'OBJECTIVE':
                return f'<div class="tc-objective"><strong>Objective:</strong><br>{inner_html}</div>'
            elif tag == 'STEPS':
                return f'<div class="tc-steps">\n{inner_html}\n</div>'
            elif tag == 'STEP':
                inner_html = self._strip_outer_p(inner_html)
                return f'<div class="tc-step">{inner_html}</div>'

            # --- Code / Data ---
            elif tag == 'FORMULA':
                raw_text = self._get_raw_text(node).strip()
                safe_formula = str(escape(raw_text))
                return f'<pre class="tc-formula"><code>{safe_formula}</code></pre>'
            elif tag == 'CODE':
                raw_text = self._get_raw_text(node).strip()
                safe_code = str(escape(raw_text))
                return f'<pre class="tc-code"><code>{safe_code}</code></pre>'
            elif tag == 'DATASET' or tag == 'TABLE':
                raw_text = self._get_raw_text(node).strip()
                return self._render_table(raw_text)

            # --- Exercise Blocks ---
            elif tag == 'TASKS':
                return f'<div class="tc-tasks">\n{inner_html}\n</div>'
            elif tag == 'TASK':
                inner_html = self._strip_outer_p(inner_html)
                return f'<div class="tc-task">{inner_html}</div>'
            elif tag == 'HINT':
                return f'<div class="tc-hint"><strong>Hint:</strong><br>{inner_html}</div>'
            elif tag == 'EXPECTED':
                return f'<div class="tc-expected"><strong>Expected Output:</strong><br>{inner_html}</div>'

            # --- Project Blocks ---
            elif tag == 'DESCRIPTION':
                return f'<div class="tc-description"><strong>Description:</strong><br>{inner_html}</div>'
            elif tag == 'REQUIREMENTS':
                return f'<div class="tc-requirements">\n<strong>Requirements:</strong><br>\n{inner_html}\n</div>'
            elif tag == 'REQUIREMENT':
                inner_html = self._strip_outer_p(inner_html)
                return f'<div class="tc-requirement">• {inner_html}</div>'
            elif tag == 'OUTPUT':
                return f'<div class="tc-output"><strong>Output:</strong><br>{inner_html}</div>'
            elif tag == 'RUBRIC':
                return f'<div class="tc-rubric">\n<strong>Rubric:</strong><br>\n{inner_html}\n</div>'
            elif tag == 'CRITERIA':
                inner_html = self._strip_outer_p(inner_html)
                return f'<div class="tc-criteria">{inner_html}</div>'

            else:
                self.errors.append({"line": node.line, "message": f"Unknown tag: [{node.tag}]"})
                return inner_html

        return ""
