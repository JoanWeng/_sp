import re


class CompletionEngine:
    LET_KWS = ['📝', '📦', '🔢', '🎈', '🚦']
    BLOCK_KWS = {'🤔': '👇', '🔁': '👇', '🛠️': '👇', '🏗️': '👇', '🎡': '👇'}

    SNIPPETS = {
        '📢': ' expression',
        '🤔': ' i 📈 0 👇',
        '🔁': ' i 📉 10 👇',
        '🎡': ' i 🟰 0 🚧 i 📉 10 🚧 i ➕ 1 👇',
        '🛠️': ' name(params) 👇',
        '🔙': ' expression',
        '🏗️': ' Name 👇',
        '🆕': ' 📋 / 📖 / StructName',
        '🤷': ' 👇',
    }

    @staticmethod
    def get_indent(line):
        return len(line) - len(line.lstrip())

    @staticmethod
    def get_line_suggestion(line_text):
        stripped = line_text.strip()
        if not stripped:
            return None

        for kw, tmpl in CompletionEngine.SNIPPETS.items():
            if stripped == kw:
                return tmpl

        for kw in CompletionEngine.LET_KWS:
            if stripped.startswith(kw):
                after = stripped[len(kw):].strip()
                if not after:
                    return None
                if '🟰' not in after:
                    return ' 🟰 value'
                if after.rstrip().endswith('🟰'):
                    return ' value'
                break

        for kw, brace in CompletionEngine.BLOCK_KWS.items():
            if kw in stripped and brace not in stripped:
                return ' ' + brace

        if '🤷' in stripped and '👇' not in stripped:
            return ' 👇'

        return None

    @staticmethod
    def get_next_line_suggestion(all_lines, cursor_line_idx):
        prev_lines = []
        for i in range(cursor_line_idx - 1, -1, -1):
            s = all_lines[i].strip()
            if s:
                prev_lines.append((i, s))

        if not prev_lines:
            return None

        last_lineno, last_line = prev_lines[0]

        if last_line == '👆' or last_line.startswith('👆'):
            return None

        if last_line.endswith('👇'):
            indent = CompletionEngine.get_indent(all_lines[cursor_line_idx]) if cursor_line_idx < len(all_lines) else 0
            return '    ' * (indent // 4 + 1) + '📢 '

        lines_before = [s for _, s in prev_lines]
        open_blocks = sum(s.count('👇') for s in lines_before) - sum(s.count('👆') for s in lines_before)
        if open_blocks > 0:
            indent = CompletionEngine.get_indent(all_lines[cursor_line_idx]) if cursor_line_idx < len(all_lines) else 0
            if indent > 0:
                return None
            block_indent = max(0, open_blocks)
            return '    ' * block_indent + '👆'

        return None

    @staticmethod
    def extract_variables(code):
        names = set()
        for kw in CompletionEngine.LET_KWS:
            pattern = re.escape(kw) + r'\s+([a-zA-Z_]\w*)'
            names.update(re.findall(pattern, code))
        return sorted(names)

    @staticmethod
    def get_variable_ghost(line_text, cursor_col, all_text):
        if cursor_col > len(line_text):
            cursor_col = len(line_text)
        start = cursor_col
        while start > 0 and (line_text[start - 1].isalnum() or line_text[start - 1] == '_'):
            start -= 1
        prefix = line_text[start:cursor_col]
        if not prefix:
            return None
        variables = CompletionEngine.extract_variables(all_text)
        if not variables:
            return None
        matches = [v for v in variables if v.startswith(prefix) and v != prefix]
        if matches:
            return matches[0][len(prefix):]
        return None
