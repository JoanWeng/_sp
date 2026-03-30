# ============================================================
#  第 3 章　習題 01 — 暫存器結構與子部分存取模擬
#  實作：模擬 x86-64 通用暫存器的 64/32/16/8-bit 子部分，
#        並展示寫入不同寬度時的 zero-extend 行為
# ============================================================

class Register:
    """
    模擬 x86-64 通用暫存器（如 RAX）的完整行為：
    - 64-bit：RXX
    - 32-bit：EXX  → 寫入時高 32 位元清零（zero-extend）
    - 16-bit：XX   → 寫入時只改低 16 位元，高 48 位元不變
    - 8-bit 低：XL → 寫入時只改最低 8 位元
    - 8-bit 高：XH → 寫入時只改 bit 8～15
    """

    def __init__(self, name: str):
        self.name = name
        self._value = 0             # 64-bit 內部值（Python int）
        self.MASK64 = 0xFFFFFFFFFFFFFFFF
        self.MASK32 = 0xFFFFFFFF
        self.MASK16 = 0xFFFF
        self.MASK8  = 0xFF

    # ── 64-bit 存取（RXX）──────────────────────────────────
    @property
    def r64(self):
        return self._value

    @r64.setter
    def r64(self, val):
        self._value = val & self.MASK64

    # ── 32-bit 存取（EXX）─ 寫入時 zero-extend 到 64-bit ──
    @property
    def r32(self):
        return self._value & self.MASK32

    @r32.setter
    def r32(self, val):
        # 關鍵行為：寫入 32-bit 會清除高 32 位元！
        self._value = val & self.MASK32   # 高 32 位元自動清零

    # ── 16-bit 存取（XX）────────────────────────────────────
    @property
    def r16(self):
        return self._value & self.MASK16

    @r16.setter
    def r16(self, val):
        # 只改低 16 位元，高 48 位元保留
        self._value = (self._value & ~self.MASK16) | (val & self.MASK16)

    # ── 8-bit 低位（XL）─────────────────────────────────────
    @property
    def r8l(self):
        return self._value & self.MASK8

    @r8l.setter
    def r8l(self, val):
        # 只改最低 8 位元，其餘保留
        self._value = (self._value & ~self.MASK8) | (val & self.MASK8)

    # ── 8-bit 高位（XH）─────────────────────────────────────
    @property
    def r8h(self):
        return (self._value >> 8) & self.MASK8

    @r8h.setter
    def r8h(self, val):
        # 只改 bit 8～15，其餘保留
        mask = self.MASK8 << 8
        self._value = (self._value & ~mask) | ((val & self.MASK8) << 8)

    def show(self, prefix=""):
        """格式化顯示暫存器各部分的值"""
        r = self._value
        print(f"{prefix}R{self.name}  = 0x{r:016X}  ({r})")
        print(f"{prefix}E{self.name}  = 0x{r & self.MASK32:08X}  ({r & self.MASK32})")
        print(f"{prefix} {self.name}  = 0x{r & self.MASK16:04X}      ({r & self.MASK16})")
        print(f"{prefix} {self.name}H = 0x{(r >> 8) & self.MASK8:02X}        ({(r >> 8) & self.MASK8})")
        print(f"{prefix} {self.name}L = 0x{r & self.MASK8:02X}        ({r & self.MASK8})")


def demo_write_behaviors():
    print("=" * 60)
    print("  暫存器子部分存取行為示範")
    print("=" * 60)

    ax = Register("AX")

    # ── 實驗 1：寫入 64-bit ──────────────────────────────
    print("\n【實驗 1】寫入 64-bit（RAX）")
    ax.r64 = 0xFFFFFFFFFFFFFFFF
    print(f"  mov rax, 0xFFFFFFFFFFFFFFFF")
    ax.show("    ")

    # ── 實驗 2：寫入 32-bit（zero-extend 行為）────────────
    print("\n【實驗 2】寫入 32-bit（EAX）→ 高 32 位元清零！")
    ax.r64 = 0xFFFFFFFFFFFFFFFF   # 先設全 1
    print(f"  mov rax, 0xFFFFFFFFFFFFFFFF  ; RAX 全為 1")
    ax.r32 = 0                     # 寫入 EAX = 0
    print(f"  mov eax, 0                   ; 寫入 EAX")
    ax.show("    ")
    print(f"  ★ 注意：整個 RAX 變成 0，高 32 位元被清除！")

    # ── 實驗 3：寫入 16-bit（只改低 16 位元）────────────
    print("\n【實驗 3】寫入 16-bit（AX）→ 只改低 16 位元")
    ax.r64 = 0xFFFFFFFFFFFFFFFF
    print(f"  mov rax, 0xFFFFFFFFFFFFFFFF")
    ax.r16 = 0
    print(f"  mov ax, 0                    ; 只寫入 AX（16-bit）")
    ax.show("    ")
    print(f"  ★ 高 48 位元保留，只有低 16 位元變為 0")

    # ── 實驗 4：寫入 8-bit（只改最低 byte）────────────────
    print("\n【實驗 4】寫入 8-bit（AL）→ 只改最低 byte")
    ax.r64 = 0xFFFFFFFFFFFFFFFF
    print(f"  mov rax, 0xFFFFFFFFFFFFFFFF")
    ax.r8l = 0
    print(f"  mov al, 0                    ; 只寫入 AL（8-bit）")
    ax.show("    ")
    print(f"  ★ 只有最低 8 位元變為 0")

    # ── 實驗 5：AH/AL 分開操作 ────────────────────────────
    print("\n【實驗 5】分別設定 AH 和 AL")
    ax.r64 = 0
    ax.r8h = 0xAB   # AH = 0xAB
    ax.r8l = 0xCD   # AL = 0xCD
    print(f"  mov ah, 0xAB")
    print(f"  mov al, 0xCD")
    ax.show("    ")
    print(f"  ★ AX = 0xABCD（AH 為高位、AL 為低位）")


def demo_all_registers():
    print("\n" + "=" * 60)
    print("  十六個通用暫存器一覽")
    print("=" * 60)

    reg_names = [
        ("AX",  "累加器 / 回傳值 / 系統呼叫編號"),
        ("BX",  "callee-saved 通用暫存器"),
        ("CX",  "計數器 / 移位量 / 第 4 參數"),
        ("DX",  "資料暫存器 / 乘除擴展 / 第 3 參數"),
        ("SP",  "★ 堆疊指標（勿隨意使用）"),
        ("BP",  "堆疊框架基底（callee-saved）"),
        ("SI",  "來源索引 / 第 2 參數（RSI）"),
        ("DI",  "目的索引 / 第 1 參數（RDI）"),
    ]

    new_regs = [
        ("R8",  "第 5 個函式參數"),
        ("R9",  "第 6 個函式參數"),
        ("R10", "caller-saved 通用"),
        ("R11", "caller-saved 通用"),
        ("R12", "callee-saved 通用"),
        ("R13", "callee-saved 通用"),
        ("R14", "callee-saved 通用"),
        ("R15", "callee-saved 通用"),
    ]

    print(f"\n{'64-bit':<8} {'32-bit':<8} {'16-bit':<8} {'8L':<6} {'8H':<6} {'用途'}")
    print("-" * 65)
    for name, usage in reg_names:
        r64 = "R" + name
        r32 = "E" + name
        r16 = name
        r8l = name[0] + "L" if len(name) == 2 else name + "L"
        r8h = name[0] + "H" if len(name) == 2 else "—"
        # SP, BP, SI, DI 的 8-bit 低位命名不同
        if name in ("SP", "BP", "SI", "DI"):
            r8l = name[0:2] + "L"
            r8h = "—"
        print(f"{r64:<8} {r32:<8} {r16:<8} {r8l:<6} {r8h:<6} {usage}")

    print("\n" + "-" * 65)
    print(f"{'64-bit':<8} {'32-bit':<8} {'16-bit':<8} {'8-bit':<6} {'用途'}")
    print("-" * 65)
    for name, usage in new_regs:
        print(f"{name:<8} {name+'D':<8} {name+'W':<8} {name+'B':<6} {'—':<6} {usage}")


def demo_abi():
    print("\n" + "=" * 60)
    print("  Linux x86-64 函式呼叫慣例（System V AMD64 ABI）")
    print("=" * 60)

    print("""
  函式參數傳遞（整數 / 指標）：
    第 1 個參數 → RDI
    第 2 個參數 → RSI
    第 3 個參數 → RDX
    第 4 個參數 → RCX
    第 5 個參數 → R8
    第 6 個參數 → R9
    第 7 個以上 → 堆疊（由右到左壓入）

  回傳值：RAX（若需要 128-bit：RAX + RDX）

  呼叫者保存（Caller-saved，被呼叫者可以任意修改）：
    RAX, RCX, RDX, RSI, RDI, R8, R9, R10, R11

  被呼叫者保存（Callee-saved，使用前必須 PUSH，返回前 POP）：
    RBX, RBP, R12, R13, R14, R15
""")

    # 模擬一次函式呼叫
    print("  模擬 func(10, 20, 30, 40, 50, 60) 的參數傳遞：")
    params = [10, 20, 30, 40, 50, 60]
    regs   = ["RDI", "RSI", "RDX", "RCX", "R8 ", "R9 "]
    for reg, val in zip(regs, params):
        print(f"    mov {reg}, {val}")
    print("    call func")
    print("    ; 回傳值在 RAX")


if __name__ == "__main__":
    demo_write_behaviors()
    demo_all_registers()
    demo_abi()