# ============================================================
#  第 5 章　習題 01 — 算術與邏輯指令模擬器
#  實作：模擬 ADD/SUB/MUL/DIV/AND/OR/XOR/NOT/SHL/SHR/SAR
#        的完整行為，包含旗標更新與結果截斷
# ============================================================

from ch03_ex02_flags import compute_flags_add, compute_flags_sub, show_flags

BITS = 32
MASK = (1 << BITS) - 1
SIGN = 1 << (BITS - 1)


def to_signed(val: int, bits: int = BITS) -> int:
    """將無號值轉為有號數解讀"""
    mask = (1 << bits) - 1
    sign = 1 << (bits - 1)
    val  = val & mask
    return val - (1 << bits) if val & sign else val


def compute_flags_logic(result: int, bits: int = BITS) -> dict:
    """AND/OR/XOR/TEST 後的旗標（CF=0, OF=0）"""
    mask = (1 << bits) - 1
    sign = 1 << (bits - 1)
    r = result & mask
    return {
        'result': r, 'bits': bits,
        'CF': 0, 'ZF': int(r == 0),
        'SF': int(bool(r & sign)),
        'OF': 0,
        'PF': int(bin(r & 0xFF).count('1') % 2 == 0),
        'AF': 0,
    }


def print_op(op: str, a: int, b: int | None, result: int,
             flags: dict, bits: int = BITS):
    """統一的結果輸出格式"""
    mask = (1 << bits) - 1
    a_s  = to_signed(a, bits)
    r_s  = to_signed(result, bits)
    r    = result & mask

    b_str = f", 0x{b & mask:X}" if b is not None else ""
    print(f"\n  {op}(0x{a & mask:X}{b_str})")
    print(f"    結果（無號）：{r}   結果（有號）：{r_s}")
    print(f"    二進位（低16）：...{r & 0xFFFF:016b}")
    print(f"    旗標：CF={flags['CF']}  ZF={flags['ZF']}  "
          f"SF={flags['SF']}  OF={flags['OF']}  PF={flags['PF']}")


# ── 算術指令 ─────────────────────────────────────────────────

def demo_arithmetic():
    print("=" * 60)
    print("  算術指令模擬（32-bit）")
    print("=" * 60)

    cases_add = [
        (100,        200,     "ADD EAX(100), EBX(200)"),
        (0x7FFFFFFF, 1,       "ADD EAX(MAX_INT), 1    → OF 溢位"),
        (0xFFFFFFFF, 1,       "ADD EAX(0xFFFFFFFF), 1 → CF 進位"),
        (0x80,       0x80,    "ADD AL(0x80), 0x80     → CF+OF", 8),
    ]

    print("\n  ── ADD ────────────────────────────────────────")
    for case in cases_add:
        if len(case) == 3:
            a, b, desc = case; bits = 32
        else:
            a, b, desc, bits = case
        mask = (1 << bits) - 1
        a, b = a & mask, b & mask
        flags = compute_flags_add(a, b, bits)
        print_op(desc, a, b, flags['result'], flags, bits)

    print("\n  ── SUB ────────────────────────────────────────")
    cases_sub = [
        (100,  30,   "SUB EAX(100), 30"),
        (5,    10,   "SUB EAX(5), 10    → CF 借位"),
        (-128, 1,    "SUB AL(-128), 1   → OF 溢位", 8),
    ]
    for case in cases_sub:
        if len(case) == 3:
            a, b, desc = case; bits = 32
        else:
            a, b, desc, bits = case
        mask = (1 << bits) - 1
        a, b = a & mask, b & mask
        flags = compute_flags_sub(a, b, bits)
        print_op(desc, a, b, flags['result'], flags, bits)

    print("\n  ── INC / DEC（注意：不影響 CF）───────────────")
    val = 0xFFFFFFFF
    # INC
    result_inc = (val + 1) & MASK
    flags_inc = compute_flags_logic(result_inc)
    flags_inc['ZF'] = int(result_inc == 0)
    flags_inc['SF'] = int(bool(result_inc & SIGN))
    # OF：從 0x7FFFFFFF 到 0x80000000
    flags_inc['OF'] = int(val == 0x7FFFFFFF)
    flags_inc['CF'] = 0   # INC 不改 CF！
    print(f"\n  INC(0x{val:08X})")
    print(f"    結果：0x{result_inc:08X}  CF={flags_inc['CF']}（不改變）"
          f"  ZF={flags_inc['ZF']}  OF={flags_inc['OF']}")

    print("\n  ── MUL（無號）────────────────────────────────")
    mul_cases = [
        (0xFF, 0xFF, 8,  "MUL AL(0xFF) × 0xFF"),
        (100,  200,  32, "MUL EAX(100) × EBX(200)"),
        (0xFFFF, 0xFFFF, 32, "MUL EAX(0xFFFF) × EBX(0xFFFF)"),
    ]
    for a, b, bits, desc in mul_cases:
        mask   = (1 << bits) - 1
        result = (a & mask) * (b & mask)
        high   = result >> bits
        low    = result & mask
        CF_OF  = int(high != 0)
        print(f"\n  {desc}")
        print(f"    全精度結果：{result}（{bits*2}-bit）")
        print(f"    高{bits}位（DX/EDX）：0x{high:0{bits//4}X}  "
              f"低{bits}位（AX/EAX）：0x{low:0{bits//4}X}")
        print(f"    CF=OF={CF_OF}（{'高位非零，有溢出' if CF_OF else '高位為零，無溢出'}）")

    print("\n  ── IMUL（有號，三運算元）──────────────────────")
    imul3_cases = [
        (10,    5,   32, "IMUL EAX, EBX(10), 5"),
        (-7,    6,   32, "IMUL EAX, EBX(-7), 6"),
        (0x7FFFFFFF, 2, 32, "IMUL EAX, EBX(MAX_INT), 2  → 溢位"),
    ]
    for b, imm, bits, desc in imul3_cases:
        mask = (1 << bits) - 1
        b_s  = to_signed(b & mask, bits)
        result_full = b_s * imm
        result      = result_full & mask
        OF = int(to_signed(result, bits) != result_full)
        print(f"\n  {desc}")
        print(f"    完整結果：{result_full}  截斷結果：{to_signed(result, bits)}"
              f"  OF={OF}{'（溢位！）' if OF else ''}")

    print("\n  ── DIV（無號）────────────────────────────────")
    div_cases = [
        (1000, 7,  "DIV EAX(1000) ÷ ECX(7)"),
        (255,  10, "DIV AX(255) ÷ BL(10)", 8),
    ]
    for case in div_cases:
        if len(case) == 3:
            dividend, divisor, desc = case; bits = 32
        else:
            dividend, divisor, desc, bits = case
        quotient  = dividend // divisor
        remainder = dividend % divisor
        print(f"\n  {desc}")
        print(f"    商（EAX/AL）：{quotient}  餘數（EDX/AH）：{remainder}")
        print(f"    驗證：{divisor} × {quotient} + {remainder} = {divisor*quotient+remainder}")


# ── 邏輯與位元指令 ───────────────────────────────────────────

def demo_logic():
    print("\n" + "=" * 60)
    print("  邏輯與位元指令模擬（8-bit 便於觀察）")
    print("=" * 60)

    bits = 8

    def show_bits(name: str, val: int):
        v = val & 0xFF
        print(f"    {name:10s} = 0b{v:08b}  (0x{v:02X} = {v})")

    cases = [
        # (op_name, a, b, 說明)
        ("AND", 0b10110101, 0b00001111, "保留低 4 位（遮罩）"),
        ("AND", 0b11111110, 0b00000001, "清除最低位（偶數對齊）"),
        ("OR",  0b10100000, 0b00001111, "設定低 4 位"),
        ("OR",  0b01000001, 0b00100000, "大寫 'A' → 小寫 'a'（OR 0x20）"),
        ("XOR", 0xFF,       0xFF,       "XOR 自身 = 0（清零）"),
        ("XOR", 0b10110101, 0b00001111, "切換低 4 位"),
        ("XOR", 0b01000001, 0b00100000, "大小寫互換（XOR 0x20）"),
    ]

    for op, a, b, desc in cases:
        a8, b8 = a & 0xFF, b & 0xFF
        if op == "AND":
            result = a8 & b8
        elif op == "OR":
            result = a8 | b8
        else:
            result = a8 ^ b8
        flags = compute_flags_logic(result, 8)

        print(f"\n  {op}：{desc}")
        show_bits("A", a8)
        show_bits("B", b8)
        show_bits("結果", result)
        print(f"    旗標：ZF={flags['ZF']}  SF={flags['SF']}  CF={flags['CF']}  OF={flags['OF']}")

    print("\n  ── NOT ────────────────────────────────────────")
    not_cases = [(0b10110101, "普通 NOT"), (0x00, "NOT 0 = 全 1"), (0xFF, "NOT 0xFF = 0")]
    for v, desc in not_cases:
        result = (~v) & 0xFF
        print(f"\n  NOT：{desc}")
        show_bits("輸入", v)
        show_bits("結果", result)
        print(f"    （NOT 不影響任何旗標）")


# ── 移位指令 ─────────────────────────────────────────────────

def demo_shift():
    print("\n" + "=" * 60)
    print("  移位指令模擬")
    print("=" * 60)

    def show_shift(op: str, val: int, count: int, bits: int = 8):
        v    = val & ((1 << bits) - 1)
        sign = 1 << (bits - 1)

        if op == "SHL":
            CF = int(bool(v & (sign >> (count - 1)))) if count <= bits else 0
            result = (v << count) & ((1 << bits) - 1)
        elif op == "SHR":
            CF = int(bool(v & (1 << (count - 1)))) if count <= bits else 0
            result = v >> count
        elif op == "SAR":
            CF = int(bool(v & (1 << (count - 1)))) if count <= bits else 0
            # 算術右移：保留符號位
            signed = v - (1 << bits) if v & sign else v
            result = (signed >> count) & ((1 << bits) - 1)
        elif op == "ROL":
            result = 0
            for _ in range(count):
                CF = (v >> (bits - 1)) & 1
                result = ((v << 1) | CF) & ((1 << bits) - 1)
                v = result
            CF = result & 1
        elif op == "ROR":
            result = 0
            for _ in range(count):
                CF = v & 1
                result = ((v >> 1) | (CF << (bits - 1))) & ((1 << bits) - 1)
                v = result
            CF = (result >> (bits - 1)) & 1
        else:
            result, CF = v, 0

        signed_r = to_signed(result, bits)
        print(f"\n  {op} {val:#010b}({v}), {count}")
        print(f"    輸入：0b{v:0{bits}b}")
        print(f"    結果：0b{result:0{bits}b}  ({result})  有號={signed_r}  CF={CF}")
        if op == "SHL":
            print(f"    等效：{v} × 2^{count} = {v * (2**count)}（若無溢位）")
        elif op in ("SHR", "SAR"):
            print(f"    等效：{to_signed(v, bits) if op=='SAR' else v} ÷ 2^{count} = "
                  f"{to_signed(v,bits)//(2**count) if op=='SAR' else v//(2**count)}")

    show_shift("SHL", 0b00000001, 4)
    show_shift("SHL", 0b10000001, 1, 8)   # CF = 1（高位移出）
    show_shift("SHR", 0b10110100, 2)
    show_shift("SAR", 0b10000000, 2)      # 負數右移（符號保留）
    show_shift("SAR", 0b01000000, 2)      # 正數右移
    show_shift("ROL", 0b10110001, 2)
    show_shift("ROR", 0b10110001, 2)

    print("""
  ── 移位的乘除法等效 ────────────────────────────────
  SHL n  =  × 2ⁿ  （無號 / 有號均可，注意 OF）
  SHR n  =  ÷ 2ⁿ  （無號整數除法，向零取整）
  SAR n  =  ÷ 2ⁿ  （有號整數除法，向負無窮取整）

  注意：SAR 和 C 的有號整數除法在負數時可能有差異！
  C 語言：-7 / 2 = -3（向零取整）
  SAR：   -7 SAR 1 = -4（向負無窮取整，-7 = 0b11111001，>>1 = 0b11111100 = -4）
""")


if __name__ == "__main__":
    demo_arithmetic()
    demo_logic()
    demo_shift()