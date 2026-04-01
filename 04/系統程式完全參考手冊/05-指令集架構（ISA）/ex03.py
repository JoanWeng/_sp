# ============================================================
#  第 5 章　習題 03 — 指令編碼與旗標影響彙整
#  實作：展示各類指令對旗標的影響規律，
#        並模擬一段組語程式的完整逐步執行過程
# ============================================================


BITS = 32
MASK = (1 << BITS) - 1
SIGN = 1 << (BITS - 1)


# ── CPU 狀態 ─────────────────────────────────────────────────

class CPUState:
    """簡易 CPU 狀態，含暫存器與旗標"""

    def __init__(self):
        self.regs = {r: 0 for r in
                     ['EAX','EBX','ECX','EDX','ESI','EDI','ESP','EBP']}
        self.flags = {'CF':0,'ZF':0,'SF':0,'OF':0,'PF':0,'AF':0,'DF':0}
        self.mem   = {}
        self.history = []

    def r(self, name: str) -> int:
        return self.regs.get(name.upper(), 0)

    def set(self, name: str, val: int):
        old = self.regs.get(name.upper(), 0)
        self.regs[name.upper()] = val & MASK
        return old

    def read32(self, addr: int) -> int:
        return self.mem.get(addr, 0)

    def write32(self, addr: int, val: int):
        self.mem[addr] = val & MASK

    def _update_flags(self, result: int, a: int, b: int | None,
                      op: str, bits: int = BITS):
        mask = (1 << bits) - 1
        sign = 1 << (bits - 1)
        r = result & mask

        self.flags['ZF'] = int(r == 0)
        self.flags['SF'] = int(bool(r & sign))
        self.flags['PF'] = int(bin(r & 0xFF).count('1') % 2 == 0)

        if op in ('ADD', 'ADC'):
            full = (a & mask) + (b & mask if b is not None else 0)
            self.flags['CF'] = int(full > mask)
            a_s = 1 if (a & sign) else 0
            b_s = 1 if (b & sign) else 0
            r_s = int(bool(r & sign))
            self.flags['OF'] = int(a_s == b_s and r_s != a_s)
            self.flags['AF'] = int(((a & 0xF) + (b & 0xF)) > 0xF)

        elif op in ('SUB', 'CMP', 'NEG'):
            b_eff = b if b is not None else 0
            self.flags['CF'] = int((a & mask) < (b_eff & mask))
            a_s = int(bool(a & sign))
            b_s = int(bool(b_eff & sign))
            r_s = int(bool(r & sign))
            self.flags['OF'] = int(a_s != b_s and r_s != a_s)
            self.flags['AF'] = int((a & 0xF) < (b_eff & 0xF))

        elif op in ('AND', 'OR', 'XOR', 'TEST'):
            self.flags['CF'] = 0
            self.flags['OF'] = 0

        elif op in ('SHL', 'SHR', 'SAR'):
            pass   # 由呼叫方設定

    def flags_str(self) -> str:
        f = self.flags
        return (f"CF={f['CF']} ZF={f['ZF']} SF={f['SF']} "
                f"OF={f['OF']} PF={f['PF']}")

    def snapshot(self) -> str:
        r = self.regs
        return (f"EAX={r['EAX']:#010x} EBX={r['EBX']:#010x} "
                f"ECX={r['ECX']:#010x} EDX={r['EDX']:#010x}  "
                + self.flags_str())


# ── 指令執行器 ───────────────────────────────────────────────

class InstructionExecutor:
    def __init__(self, cpu: CPUState):
        self.cpu = cpu

    def _log(self, asm: str, note: str = ""):
        snap = self.cpu.snapshot()
        self.cpu.history.append((asm, snap, note))
        print(f"  {asm:<30}  →  {snap}")
        if note:
            print(f"  {'':30}     ↳ {note}")

    def mov(self, dst: str, val: int, asm: str = ""):
        self.cpu.set(dst, val)
        self._log(asm or f"MOV {dst}, {val:#x}")

    def add(self, dst: str, val: int, asm: str = ""):
        a = self.cpu.r(dst)
        b = val & MASK
        result = a + b
        self.cpu.set(dst, result)
        self.cpu._update_flags(result, a, b, 'ADD')
        self._log(asm or f"ADD {dst}, {val:#x}")

    def sub(self, dst: str, val: int, asm: str = ""):
        a = self.cpu.r(dst)
        b = val & MASK
        result = a - b
        self.cpu.set(dst, result)
        self.cpu._update_flags(result, a, b, 'SUB')
        self._log(asm or f"SUB {dst}, {val:#x}")

    def inc(self, dst: str, asm: str = ""):
        cf_save = self.cpu.flags['CF']  # INC 不改 CF
        a = self.cpu.r(dst)
        result = a + 1
        self.cpu.set(dst, result)
        self.cpu._update_flags(result, a, 1, 'ADD')
        self.cpu.flags['CF'] = cf_save   # 還原 CF
        self._log(asm or f"INC {dst}")

    def dec(self, dst: str, asm: str = ""):
        cf_save = self.cpu.flags['CF']
        a = self.cpu.r(dst)
        result = a - 1
        self.cpu.set(dst, result)
        self.cpu._update_flags(result, a, 1, 'SUB')
        self.cpu.flags['CF'] = cf_save
        self._log(asm or f"DEC {dst}")

    def xor(self, dst: str, src_val: int, asm: str = ""):
        a = self.cpu.r(dst)
        result = a ^ (src_val & MASK)
        self.cpu.set(dst, result)
        self.cpu._update_flags(result, a, src_val, 'XOR')
        self._log(asm or f"XOR {dst}, {src_val:#x}")

    def and_(self, dst: str, val: int, asm: str = ""):
        a = self.cpu.r(dst)
        result = a & (val & MASK)
        self.cpu.set(dst, result)
        self.cpu._update_flags(result, a, val, 'AND')
        self._log(asm or f"AND {dst}, {val:#x}")

    def shl(self, dst: str, count: int, asm: str = ""):
        a = self.cpu.r(dst)
        CF = int(bool(a & (SIGN >> (count - 1)))) if 0 < count <= BITS else 0
        result = (a << count) & MASK
        self.cpu.set(dst, result)
        self.cpu._update_flags(result, a, None, 'SHL')
        self.cpu.flags['CF'] = CF
        self._log(asm or f"SHL {dst}, {count}")

    def shr(self, dst: str, count: int, asm: str = ""):
        a = self.cpu.r(dst)
        CF = int(bool(a & (1 << (count - 1)))) if 0 < count <= BITS else 0
        result = a >> count
        self.cpu.set(dst, result)
        self.cpu._update_flags(result, a, None, 'SHR')
        self.cpu.flags['CF'] = CF
        self._log(asm or f"SHR {dst}, {count}")

    def cmp(self, dst: str, val: int, asm: str = ""):
        a = self.cpu.r(dst)
        b = val & MASK
        result = a - b
        self.cpu._update_flags(result, a, b, 'SUB')
        self._log(asm or f"CMP {dst}, {val:#x}", "（只設旗標，不改暫存器）")

    def test(self, dst: str, val: int, asm: str = ""):
        a = self.cpu.r(dst)
        result = a & (val & MASK)
        self.cpu._update_flags(result, a, val, 'AND')
        self._log(asm or f"TEST {dst}, {val:#x}", "（只設旗標，不改暫存器）")


# ── 旗標影響彙整 ─────────────────────────────────────────────

def demo_flag_impact():
    print("=" * 70)
    print("  各類指令對旗標的影響彙整")
    print("=" * 70)

    table = [
        ("ADD / ADC",       "✓", "✓", "✓", "✓", "✓", "✓"),
        ("SUB / SBB / CMP", "✓", "✓", "✓", "✓", "✓", "✓"),
        ("NEG",             "✓", "✓", "✓", "✓", "✓", "✓"),
        ("INC / DEC",       "—", "✓", "✓", "✓", "✓", "✓"),
        ("MUL / IMUL",      "✓", "—", "—", "✓", "—", "—"),
        ("DIV / IDIV",      "?", "?", "?", "?", "?", "?"),
        ("AND/OR/XOR/TEST", "0", "✓", "✓", "0", "✓", "—"),
        ("NOT",             "—", "—", "—", "—", "—", "—"),
        ("SHL/SHR/SAR(1)",  "✓", "✓", "✓", "✓", "✓", "—"),
        ("SHL/SHR/SAR(n)",  "✓", "✓", "✓", "?", "✓", "—"),
        ("ROL/ROR",         "✓", "—", "—", "✓*","—", "—"),
        ("MOV / LEA",       "—", "—", "—", "—", "—", "—"),
        ("PUSH / POP",      "—", "—", "—", "—", "—", "—"),
        ("CALL / RET",      "—", "—", "—", "—", "—", "—"),
    ]

    header = f"  {'指令類別':<22} {'CF':>4} {'ZF':>4} {'SF':>4} {'OF':>4} {'PF':>4} {'AF':>4}"
    print(f"\n{header}")
    print("  " + "-" * 50)
    for row in table:
        name, *flags = row
        vals = "".join(f"{f:>4}" for f in flags)
        print(f"  {name:<22} {vals}")

    print("""
  圖例：
    ✓  : 依結果更新
    0  : 強制清零
    —  : 不影響（保留原值）
    ?  : 未定義（值不可預測）
    ✓* : 只在移位量 = 1 時定義
  
  重點提醒：
    · INC/DEC 不影響 CF（多精度加法中不能用 INC 替代 ADD 1）
    · AND/OR/XOR 永遠清除 CF 和 OF
    · NOT 完全不影響任何旗標
    · MOV/LEA/PUSH/POP 完全不影響任何旗標
""")


# ── 逐步執行模擬 ─────────────────────────────────────────────

def demo_step_execution():
    print("=" * 70)
    print("  逐步執行模擬：計算 GCD（最大公因數）")
    print("=" * 70)

    print("""
  對應 C 程式碼：
    // 計算 GCD(a, b) 使用輾轉相除法
    int gcd(int a, int b) {
        while (b != 0) {
            int t = b;
            b = a % b;
            a = t;
        }
        return a;
    }
    gcd(48, 18)  // 預期結果：6
  
  組語（EAX = a, EBX = b）：
    MOV EAX, 48
    MOV EBX, 18
  .loop:
    TEST EBX, EBX       ; b == 0?
    JZ   .done
    MOV  EDX, 0
    MOV  ECX, EBX       ; ECX = b
    DIV  ECX            ; EAX = a/b，EDX = a%b
    MOV  EAX, ECX       ; a = 舊 b
    MOV  EBX, EDX       ; b = a % b
    JMP  .loop
  .done:
    ; EAX = GCD
  
  逐步執行：
""")

    print(f"  {'指令':<30}  {'EAX':>12} {'EBX':>12} {'ECX':>12} {'EDX':>12}  {'旗標'}")
    print("  " + "-" * 95)

    def run_gcd(a, b):
        EAX, EBX = a, b
        ECX, EDX = 0, 0
        CF, ZF, SF, OF, PF = 0, 0, 0, 0, 0
        iteration = 0

        def print_state(asm, note=""):
            flags = f"ZF={ZF}"
            print(f"  {asm:<30}  {EAX:>12} {EBX:>12} {ECX:>12} {EDX:>12}  {flags}"
                  + (f"  ← {note}" if note else ""))

        print_state(f"MOV EAX, {a}", f"a={a}")
        print_state(f"MOV EBX, {b}", f"b={b}")

        while True:
            iteration += 1
            ZF = int(EBX == 0)
            print_state(f"TEST EBX, EBX  [iter {iteration}]", "b==0?" if ZF else "b≠0，繼續")
            if ZF:
                break
            ECX = EBX
            EDX = EAX % EBX
            EAX_new = EBX
            print_state(f"DIV ECX({ECX})", f"{EAX}÷{EBX}=商{EAX//EBX}餘{EDX}")
            EAX = EAX_new
            EBX = EDX
            print_state(f"MOV EAX←{EAX}, EBX←{EBX}")

        return EAX

    result = run_gcd(48, 18)
    print(f"\n  GCD(48, 18) = {result}  {'✓' if result == 6 else '✗'}")

    print()
    result2 = run_gcd(100, 75)
    print(f"\n  GCD(100, 75) = {result2}  {'✓' if result2 == 25 else '✗'}")


def demo_instruction_categories():
    print("\n" + "=" * 70)
    print("  指令類別與常用慣用法速查")
    print("=" * 70)

    idioms = [
        ("清零暫存器",        "XOR EAX, EAX",        "比 MOV EAX,0 短 1 byte"),
        ("測試是否為零",      "TEST EAX, EAX",       "比 CMP EAX,0 短 1 byte"),
        ("×2",               "SHL EAX, 1 或 ADD EAX,EAX", "移位比 IMUL 快"),
        ("×3",               "LEA EAX, [EAX+EAX*2]","LEA 完成乘法+賦值"),
        ("×5",               "LEA EAX, [EAX+EAX*4]","一條指令"),
        ("×10",              "LEA EAX,[EAX+EAX*4]\n  ADD EAX,EAX",   "兩條指令"),
        ("÷2（無號）",        "SHR EAX, 1",          "移位比 DIV 快很多"),
        ("÷2（有號）",        "SAR EAX, 1",          "保留符號位"),
        ("取絕對值",          "CDQ\n  XOR EAX,EDX\n  SUB EAX,EDX", "無分支實作"),
        ("計算負數",          "NEG EAX",             "等同 NOT EAX; INC EAX"),
        ("判斷最低位",        "TEST EAX, 1",         "奇數：ZF=0；偶數：ZF=1"),
        ("大小寫轉換",        "OR AL, 0x20",         "大→小寫（'A'+0x20='a'）"),
        ("大小寫互換",        "XOR AL, 0x20",        "切換大小寫"),
        ("交換兩值",          "XCHG EAX, EBX",       "不需臨時變數"),
        ("NOP 等效",          "XCHG EAX, EAX",       "機器碼 0x90"),
    ]

    print(f"\n  {'用途':<16} {'慣用組語':<40} {'說明'}")
    print("  " + "-" * 80)
    for purpose, asm, note in idioms:
        asm_lines = asm.split('\n')
        print(f"  {purpose:<16} {asm_lines[0]:<40} {note}")
        for extra_line in asm_lines[1:]:
            print(f"  {'':16} {extra_line:<40}")


if __name__ == "__main__":
    demo_flag_impact()
    demo_step_execution()
    demo_instruction_categories()