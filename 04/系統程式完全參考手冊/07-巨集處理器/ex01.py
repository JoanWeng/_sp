# ============================================================
#  第 7 章　習題 01 — 巨集處理器模擬器
#  實作：模擬巨集名稱表(MNT)、巨集定義表(MDT)的建立，
#        以及帶參數巨集的展開流程（含唯一標號產生）
# ============================================================

import re
from dataclasses import dataclass

@dataclass
class MacroEntry:
    name:      str
    n_params:  int
    body:      list
    mnt_index: int = 0

class MacroProcessor:
    def __init__(self):
        self.mnt: dict = {}
        self.mdt: list = []
        self._label_counter = 0
        self.expansion_log: list = []

    def pass1(self, source_lines):
        remaining = []
        i = 0
        while i < len(source_lines):
            line = source_lines[i].strip()
            if line.lower().startswith('%macro'):
                parts    = line.split()
                name     = parts[1]
                n_params = int(parts[2]) if len(parts) > 2 else 0
                body_lines = []
                i += 1
                while i < len(source_lines):
                    bline = source_lines[i].strip()
                    if bline.lower() == '%endmacro':
                        break
                    normalized = re.sub(r'%(\d+)', r'?\1', bline)
                    body_lines.append(normalized)
                    i += 1
                mdt_start = len(self.mdt)
                self.mdt.extend(body_lines)
                entry = MacroEntry(name=name, n_params=n_params,
                                   body=body_lines, mnt_index=mdt_start)
                self.mnt[name.upper()] = entry
            else:
                if line and not line.startswith(';'):
                    remaining.append(line)
            i += 1
        return remaining

    def pass2(self, lines):
        output = []
        for line in lines:
            output.extend(self._try_expand(line))
        return output

    def _try_expand(self, line):
        tokens = line.split(None, 1)
        if not tokens:
            return [line]
        macro_name = tokens[0].upper()
        if macro_name not in self.mnt:
            return [line]
        entry = self.mnt[macro_name]
        args = [a.strip() for a in tokens[1].split(',')] if len(tokens) > 1 else []
        self._label_counter += 1
        prefix = f'..@{self._label_counter}'
        self.expansion_log.append(
            f"  展開 {macro_name}({', '.join(args)}) → {len(entry.body)} 行  [前綴 {prefix}]")
        expanded = []
        for bline in entry.body:
            r = bline
            for i, arg in enumerate(args, 1):
                r = r.replace(f'?{i}', arg)
            r = re.sub(r'%%(\w+)', f'{prefix}.\\1', r)
            expanded.append(r)
        return expanded

    def print_mnt(self):
        print(f"\n  巨集名稱表（MNT）：")
        print(f"  {'名稱':<16} {'引數數':>6} {'MDT起始':>8} {'主體行數':>8}")
        print(f"  {'─'*42}")
        for name, e in self.mnt.items():
            print(f"  {name:<16} {e.n_params:>6} {e.mnt_index:>8} {len(e.body):>8}")

    def print_mdt(self):
        print(f"\n  巨集定義表（MDT）：")
        print(f"  {'行號':>4}  內容")
        print(f"  {'─'*50}")
        for i, line in enumerate(self.mdt):
            print(f"  {i:>4}  {line}")

    def process(self, source):
        lines = [l for l in source.strip().splitlines()]
        remaining = self.pass1(lines)
        return self.pass2(remaining)


def demo_basic_expansion():
    print("=" * 65)
    print("  示範 1：基本巨集展開（無參數 / 有參數）")
    print("=" * 65)
    source = """\
%macro EXIT_OK 0
    MOV  RAX, 60
    XOR  RDI, RDI
    SYSCALL
%endmacro
%macro PRINT_STR 2
    MOV  RAX, 1
    MOV  RDI, 1
    LEA  RSI, [%1]
    MOV  RDX, %2
    SYSCALL
%endmacro
_start:
    PRINT_STR hello, hello_len
    PRINT_STR world, world_len
    EXIT_OK
"""
    mp = MacroProcessor()
    result = mp.process(source)
    mp.print_mnt()
    mp.print_mdt()
    print(f"\n  展開記錄：")
    for log in mp.expansion_log:
        print(log)
    print(f"\n  展開後的程式碼：")
    for i, line in enumerate(result, 1):
        print(f"  {i:>3}:  {line}")


def demo_label_expansion():
    print("\n" + "=" * 65)
    print("  示範 2：%%label 唯一標號展開")
    print("=" * 65)
    source = """\
%macro MAX_OF 3
    MOV  EAX, %1
    CMP  EAX, %2
    JGE  %%already_max
    MOV  EAX, %2
%%already_max:
    MOV  %3, EAX
%endmacro
    MAX_OF EBX, ECX, EAX
    MAX_OF EDX, ESI, EBX
    MAX_OF ECX, EDI, ECX
"""
    mp = MacroProcessor()
    result = mp.process(source)
    print(f"\n  展開記錄：")
    for log in mp.expansion_log:
        print(log)
    print(f"\n  展開後的程式碼（每次展開的標號名稱不同）：")
    for i, line in enumerate(result, 1):
        marker = " ← 唯一標號" if '..@' in line else ""
        print(f"  {i:>3}:  {line:<40}{marker}")


def demo_mdt_mnt_structure():
    print("\n" + "=" * 65)
    print("  示範 3：MDT / MNT 完整結構")
    print("=" * 65)
    source = """\
%macro SYS_EXIT 1
    MOV  RAX, 60
    MOV  RDI, %1
    SYSCALL
%endmacro
%macro SYS_WRITE 3
    MOV  RAX, 1
    MOV  RDI, %1
    LEA  RSI, [%2]
    MOV  RDX, %3
    SYSCALL
%endmacro
    SYS_WRITE 1, msg, 13
    SYS_EXIT 0
"""
    mp = MacroProcessor()
    result = mp.process(source)
    mp.print_mnt()
    mp.print_mdt()
    print(f"\n  展開後的程式碼：")
    for i, line in enumerate(result, 1):
        print(f"  {i:>3}:  {line}")


if __name__ == "__main__":
    demo_basic_expansion()
    demo_label_expansion()
    demo_mdt_mnt_structure()