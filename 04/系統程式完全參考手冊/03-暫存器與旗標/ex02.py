# ============================================================
#  第 3 章　習題 02 — 旗標暫存器（FLAGS）模擬器
#  實作：模擬加減法後的 CF/ZF/SF/OF/PF/AF 旗標計算，
#        並展示 CMP/TEST 與條件跳躍的完整流程
# ============================================================

def compute_flags_add(a: int, b: int, bits: int = 32) -> dict:
    """
    模擬 ADD a, b 後的旗標狀態（不含 DF/IF）。

    參數：
        a, b：運算元（Python int）
        bits：運算元寬度（8 / 16 / 32 / 64）
    回傳：
        dict，包含 result 及各旗標值
    """
    mask     = (1 << bits) - 1
    sign_bit = 1 << (bits - 1)

    result_full = a + b         # 不截斷的完整結果（用於 CF）
    result      = result_full & mask

    # CF：無號溢位（結果超過 mask）
    CF = 1 if result_full > mask else 0

    # ZF：結果為零
    ZF = 1 if result == 0 else 0

    # SF：最高位元（結果的符號位）
    SF = 1 if (result & sign_bit) != 0 else 0

    # OF：有號溢位（兩個正數相加得負，或兩個負數相加得正）
    a_sign = 1 if (a & sign_bit) != 0 else 0
    b_sign = 1 if (b & sign_bit) != 0 else 0
    r_sign = SF
    OF = 1 if (a_sign == b_sign) and (r_sign != a_sign) else 0

    # PF：最低 8 位元中 1 的個數為偶數
    low_byte = result & 0xFF
    PF = 1 if bin(low_byte).count('1') % 2 == 0 else 0

    # AF：bit 3 向 bit 4 進位
    AF = 1 if ((a & 0xF) + (b & 0xF)) > 0xF else 0

    return {
        'result': result, 'bits': bits,
        'CF': CF, 'ZF': ZF, 'SF': SF, 'OF': OF, 'PF': PF, 'AF': AF
    }


def compute_flags_sub(a: int, b: int, bits: int = 32) -> dict:
    """
    模擬 SUB a, b（或 CMP a, b）後的旗標狀態。
    SUB 的旗標等同於加上 b 的二補數：a + (~b + 1)
    """
    mask     = (1 << bits) - 1
    sign_bit = 1 << (bits - 1)

    result_full = a - b
    result      = result_full & mask

    # CF：無號借位（a < b，無號數）
    CF = 1 if a < b else 0

    # ZF：結果為零
    ZF = 1 if result == 0 else 0

    # SF：最高位元
    SF = 1 if (result & sign_bit) != 0 else 0

    # OF：有號溢位（正-負=負，或負-正=正）
    a_sign = 1 if (a & sign_bit) != 0 else 0
    b_sign = 1 if (b & sign_bit) != 0 else 0
    r_sign = SF
    OF = 1 if (a_sign != b_sign) and (r_sign != a_sign) else 0

    # PF：最低 8 位元中 1 的個數
    low_byte = result & 0xFF
    PF = 1 if bin(low_byte).count('1') % 2 == 0 else 0

    # AF：bit 3 借位
    AF = 1 if (a & 0xF) < (b & 0xF) else 0

    return {
        'result': result, 'bits': bits,
        'CF': CF, 'ZF': ZF, 'SF': SF, 'OF': OF, 'PF': PF, 'AF': AF
    }


def show_flags(flags: dict, op_str: str):
    """格式化顯示旗標計算結果"""
    bits = flags['bits']
    mask = (1 << bits) - 1
    r    = flags['result']

    print(f"\n  指令：{op_str}")
    print(f"  結果：0x{r:0{bits//4}X}  ({r})  "
          f"有號：{r if r < (1 << (bits-1)) else r - (1 << bits)}")
    print(f"  二進位：{r:0{bits}b}" if bits <= 16 else
          f"  二進位（低16位）：...{r & 0xFFFF:016b}")
    print(f"  旗標：  CF={flags['CF']}  ZF={flags['ZF']}  "
          f"SF={flags['SF']}  OF={flags['OF']}  "
          f"PF={flags['PF']}  AF={flags['AF']}")


def explain_flags(flags: dict):
    """解釋各旗標的含義"""
    lines = []
    if flags['CF']:
        lines.append("    CF=1 → 無號數運算發生進位/借位")
    if flags['ZF']:
        lines.append("    ZF=1 → 結果為零")
    if flags['SF']:
        lines.append("    SF=1 → 結果的最高位元為 1（有號數為負）")
    if flags['OF']:
        lines.append("    OF=1 → 有號數溢位（結果超出有號數範圍）")
    if flags['PF']:
        lines.append("    PF=1 → 低 8 位元中 1 的個數為偶數")
    if not any([flags['CF'], flags['ZF'], flags['SF'], flags['OF']]):
        lines.append("    所有主要旗標為 0（正常無溢位結果）")
    for l in lines:
        print(l)


# ── 條件跳躍判斷 ─────────────────────────────────────────────

def would_jump(instr: str, flags: dict) -> bool:
    """判斷給定旗標下，條件跳躍指令是否會發生跳躍"""
    CF = flags['CF']
    ZF = flags['ZF']
    SF = flags['SF']
    OF = flags['OF']
    PF = flags['PF']

    table = {
        # 基於單一旗標
        'JE':  ZF == 1,
        'JZ':  ZF == 1,
        'JNE': ZF == 0,
        'JNZ': ZF == 0,
        'JC':  CF == 1,
        'JNC': CF == 0,
        'JS':  SF == 1,
        'JNS': SF == 0,
        'JO':  OF == 1,
        'JNO': OF == 0,
        'JP':  PF == 1,
        'JNP': PF == 0,
        # 無號數比較
        'JA':  CF == 0 and ZF == 0,
        'JAE': CF == 0,
        'JNB': CF == 0,
        'JB':  CF == 1,
        'JNAE':CF == 1,
        'JBE': CF == 1 or ZF == 1,
        'JNA': CF == 1 or ZF == 1,
        # 有號數比較
        'JG':  ZF == 0 and SF == OF,
        'JNLE':ZF == 0 and SF == OF,
        'JGE': SF == OF,
        'JNL': SF == OF,
        'JL':  SF != OF,
        'JNGE':SF != OF,
        'JLE': ZF == 1 or SF != OF,
        'JNG': ZF == 1 or SF != OF,
    }
    return table.get(instr.upper(), False)


def demo_add_flags():
    print("=" * 60)
    print("  ADD 指令的旗標計算（32-bit）")
    print("=" * 60)

    cases = [
        (100,   200,   "ADD EAX(100),   EBX(200)    → 普通加法"),
        (0xFF,    1,   "ADD AL(0xFF),    1           → 8-bit CF 溢位"),
        (127,     1,   "ADD AL(127),     1           → 8-bit OF 溢位（有號）", 8),
        (0x7FFFFFFF, 1,"ADD EAX(MAX_INT),1           → 32-bit OF 溢位"),
        (0,       0,   "ADD EAX(0),      0           → ZF=1"),
        (0x80,  0x80,  "ADD AL(0x80),    0x80        → CF=1 且 OF=1", 8),
    ]

    for case in cases:
        if len(case) == 3:
            a, b, desc = case
            bits = 32
        else:
            a, b, desc, bits = case
        mask = (1 << bits) - 1
        a, b = a & mask, b & mask
        flags = compute_flags_add(a, b, bits)
        print(f"\n  {desc}")
        show_flags(flags, f"ADD  0x{a:X},  0x{b:X}  ({bits}-bit)")
        explain_flags(flags)


def demo_cmp_and_jump():
    print("\n" + "=" * 60)
    print("  CMP 指令 + 條件跳躍（有號 vs 無號）")
    print("=" * 60)

    print("""
  關鍵：CMP a, b 等同於 SUB a, b 但不儲存結果
  有號數比較用 JG/JL/JGE/JLE
  無號數比較用 JA/JB/JAE/JBE
""")

    cases_cmp = [
        (10,  20, 32, "CMP EAX(10),  EBX(20)"),
        (20,  10, 32, "CMP EAX(20),  EBX(10)"),
        (10,  10, 32, "CMP EAX(10),  EBX(10)"),
        # 有號 vs 無號解讀差異：-1 vs 1
        (0xFFFFFFFF, 1, 32, "CMP EAX(0xFFFFFFFF = -1 有號 / 4294967295 無號),  1"),
    ]

    jumps_signed   = ['JG', 'JGE', 'JL', 'JLE', 'JE', 'JNE']
    jumps_unsigned = ['JA', 'JAE', 'JB', 'JBE', 'JE', 'JNE']

    for a, b, bits, desc in cases_cmp:
        mask = (1 << bits) - 1
        a, b = a & mask, b & mask
        flags = compute_flags_sub(a, b, bits)
        print(f"\n  {desc}")
        show_flags(flags, f"CMP  0x{a:X},  0x{b:X}")

        a_signed = a if a < (1 << (bits-1)) else a - (1 << bits)
        b_signed = b if b < (1 << (bits-1)) else b - (1 << bits)

        print(f"\n  有號數條件跳躍（a={a_signed}, b={b_signed}）：")
        for j in jumps_signed:
            result = would_jump(j, flags)
            mark   = "會跳 ✓" if result else "不跳  "
            print(f"    {j:<6} → {mark}")

        print(f"\n  無號數條件跳躍（a={a}, b={b}）：")
        for j in jumps_unsigned:
            result = would_jump(j, flags)
            mark   = "會跳 ✓" if result else "不跳  "
            print(f"    {j:<6} → {mark}")


def demo_overflow_vs_carry():
    print("\n" + "=" * 60)
    print("  CF（無號溢位）vs OF（有號溢位）差異")
    print("=" * 60)

    print("""
  同一個位元模式，用無號數還是有號數解讀，含義不同。
  CF 對應無號溢位，OF 對應有號溢位。
""")

    cases = [
        (0x7F, 0x01, 8, "正+正=負（OF 但無 CF）"),
        (0xFF, 0x01, 8, "無號溢位（CF 但無 OF）"),
        (0x80, 0x80, 8, "CF=1 且 OF=1"),
        (0x40, 0x20, 8, "正常加法（CF=0, OF=0）"),
    ]

    for a, b, bits, desc in cases:
        flags = compute_flags_add(a, b, bits)
        a_s = a if a < (1 << (bits-1)) else a - (1 << bits)
        b_s = b if b < (1 << (bits-1)) else b - (1 << bits)
        r   = flags['result']
        r_s = r if r < (1 << (bits-1)) else r - (1 << bits)
        print(f"\n  {desc}")
        print(f"    {a_s:4d}({a:#04x}) + {b_s:4d}({b:#04x})"
              f" = {r_s:4d}({r:#04x})  CF={flags['CF']}  OF={flags['OF']}")
        if flags['CF']:
            print(f"    無號：{a} + {b} = {a+b}（超出 0～{(1<<bits)-1}，溢位）")
        if flags['OF']:
            lo, hi = -(1 << (bits-1)), (1 << (bits-1)) - 1
            print(f"    有號：{a_s} + {b_s} = {a_s+b_s}（超出 {lo}～{hi}，溢位）")


if __name__ == "__main__":
    demo_add_flags()
    demo_cmp_and_jump()
    demo_overflow_vs_carry()