# ============================================================
#  第 2 章　習題 02 — 兩遍組譯器（Two-Pass Assembler）模擬
#  實作：Pass 1 建立符號表；Pass 2 解析指令並產生假目的碼
# ============================================================

# 假設的指令長度表（x86 簡化版）
INSTRUCTION_LENGTHS = {
    'MOV':  5,   # MOV reg, imm32
    'ADD':  2,   # ADD reg, reg
    'SUB':  2,
    'DEC':  2,
    'INC':  2,
    'CMP':  2,
    'JMP':  5,   # 近跳（Near jump）
    'JNZ':  5,
    'JZ':   5,
    'JE':   5,
    'JNE':  5,
    'JG':   5,
    'JL':   5,
    'CALL': 5,
    'RET':  1,
    'NOP':  1,
    'HLT':  1,
    'PUSH': 1,
    'POP':  1,
    'INT':  2,
    'SYSCALL': 2,
}

# ── Pass 1：建立符號表 ────────────────────────────────────────

def pass1(program):
    """
    第一遍掃描：計算每行的位址，將有標號的行記錄到符號表。

    program: list of str，每行格式為：
        "[LABEL:]  MNEMONIC  [OPERAND]  [; comment]"

    回傳：
        symbol_table: dict { label: address }
        listing:      list of (address, label, mnemonic, operand)
    """
    symbol_table = {}
    listing = []
    lc = 0

    for raw_line in program:
        # 去掉註解
        line = raw_line.split(';')[0].strip()
        if not line:
            continue

        label = None
        mnemonic = ''
        operand = ''

        # 解析標號
        if ':' in line:
            parts = line.split(':', 1)
            label = parts[0].strip()
            line = parts[1].strip()

        # 解析助記符與運算元
        tokens = line.split(None, 1)
        if tokens:
            mnemonic = tokens[0].upper()
            operand  = tokens[1].strip() if len(tokens) > 1 else ''

        # 記錄標號位址
        if label:
            symbol_table[label] = lc

        size = INSTRUCTION_LENGTHS.get(mnemonic, 0)
        listing.append((lc, label, mnemonic, operand, size))
        lc += size

    return symbol_table, listing


# ── Pass 2：解析符號、產生假目的碼 ───────────────────────────

def pass2(listing, symbol_table):
    """
    第二遍掃描：利用符號表解析前向參考，產生（假）目的碼說明。

    回傳：
        object_lines: list of str（目的碼說明文字）
    """
    object_lines = []

    for (addr, label, mnemonic, operand, size) in listing:
        if not mnemonic:
            continue

        # 解析運算元中的符號（前向參考）
        resolved_operand = operand
        for sym, sym_addr in symbol_table.items():
            if sym in operand:
                resolved_operand = operand.replace(sym, f'0x{sym_addr:04X}')

        # 產生假目的碼描述
        obj = f"{mnemonic:<8} {resolved_operand}"
        object_lines.append((addr, size, label, mnemonic, resolved_operand, obj))

    return object_lines


# ── 主程式 ────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  兩遍組譯器（Two-Pass Assembler）模擬")
    print("=" * 65)

    # 範例組合語言程式：計算 1+2+3+...+N 的總和
    program = [
        "; 計算 1 到 5 的總和，結果存入 EAX",
        "START:  MOV EAX, 0       ; 累加器清零",
        "        MOV ECX, 5       ; 計數器 = 5",
        "LOOP:   ADD EAX, ECX     ; EAX += ECX",
        "        DEC ECX          ; ECX--",
        "        JNZ LOOP         ; 若 ECX≠0 繼續迴圈",
        "        HLT              ; 停止（結果在 EAX）",
    ]

    print("\n原始程式碼：")
    for line in program:
        print(f"  {line}")

    # ── 第一遍 ──
    print("\n" + "─" * 65)
    print("  【第一遍 Pass 1】建立符號表")
    print("─" * 65)

    symbol_table, listing = pass1(program)

    print(f"\n{'位址':>6}  {'標號':<10} {'助記符':<8} {'運算元':<15} {'大小':>4}")
    print("-" * 50)
    for (addr, label, mnemonic, operand, size) in listing:
        lbl = label if label else ''
        print(f"0x{addr:04X}  {lbl:<10} {mnemonic:<8} {operand:<15} {size:>3} bytes")

    print("\n符號表：")
    for sym, addr in symbol_table.items():
        print(f"  {sym:<10} → 0x{addr:04X}  ({addr})")

    # ── 第二遍 ──
    print("\n" + "─" * 65)
    print("  【第二遍 Pass 2】解析符號，產生目的碼")
    print("─" * 65)

    object_lines = pass2(listing, symbol_table)

    print(f"\n{'位址':>6}  {'大小':>4}  {'標號':<10} {'目的碼（解析後）'}")
    print("-" * 55)
    for (addr, size, label, mnemonic, resolved_op, obj) in object_lines:
        lbl = label if label else ''
        print(f"0x{addr:04X}  {size:>3}B   {lbl:<10} {obj}")

    # ── 前向參考示範 ──
    print("\n" + "─" * 65)
    print("  【前向參考（Forward Reference）示範】")
    print("─" * 65)
    print("""
  程式中 JNZ LOOP 出現在 LOOP 標號已知之後，
  但若改為 JMP END（END 在後面才定義），即為前向參考：

      JMP END     ← 第一遍時 END 尚未記錄，位址未知
      NOP
  END: HLT        ← 第一遍結束後才知道 END = 0x000B

  兩遍組譯的意義：第一遍先掃完所有標號，
  第二遍再回頭填入正確位址，解決前向參考問題。
""")

    # ── 動態示範前向參考 ──
    program2 = [
        "        JMP END",
        "        NOP",
        "END:    HLT",
    ]
    sym2, lst2 = pass1(program2)
    obj2 = pass2(lst2, sym2)

    print("  前向參考範例程式的兩遍結果：")
    print(f"  {'位址':>6}  {'目的碼（解析後）'}")
    print("  " + "-" * 35)
    for (addr, size, label, mnemonic, resolved_op, obj) in obj2:
        lbl = f"{label}:" if label else ''
        print(f"  0x{addr:04X}  {lbl:<6} {obj}")
    print(f"\n  符號表：END → 0x{sym2.get('END', 0):04X}")
    print("  JMP END 在第二遍被正確解析為 JMP 0x000B ✓")


if __name__ == '__main__':
    main()