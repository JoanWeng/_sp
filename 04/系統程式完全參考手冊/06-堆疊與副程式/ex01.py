# ============================================================
#  第 6 章　習題 01 — 堆疊框架與呼叫慣例模擬
#  實作：完整模擬函式呼叫的堆疊框架建立、參數傳遞、
#        區域變數存取、callee-saved 保存與返回過程
# ============================================================

import textwrap


class Stack:
    """模擬 x86-64 堆疊（向低位址成長）"""

    def __init__(self, base: int = 0x7FFF_0000, size: int = 1024):
        self.mem    = {}
        self.RSP    = base
        self.RBP    = 0
        self.base   = base

    def push(self, value: int, label: str = "") -> int:
        self.RSP -= 8
        self.mem[self.RSP] = value & 0xFFFF_FFFF_FFFF_FFFF
        return self.RSP

    def pop(self) -> int:
        val = self.mem.pop(self.RSP, 0)
        self.RSP += 8
        return val

    def read(self, addr: int) -> int:
        return self.mem.get(addr, 0xDEAD_BEEF_DEAD_BEEF)

    def write(self, addr: int, value: int):
        self.mem[addr] = value & 0xFFFF_FFFF_FFFF_FFFF

    def sub_rsp(self, n: int):
        self.RSP -= n

    def add_rsp(self, n: int):
        self.RSP += n

    def show(self, title: str = "", highlight: dict = None):
        """顯示堆疊快照，highlight = {addr: 說明}"""
        print(f"\n  {'─'*3} {title} {'─'*(40-len(title))}")
        print(f"  {'位址':>12}  {'值（hex）':>18}  {'偏移 RBP':>10}  說明")
        print(f"  {'─'*65}")
        addrs = sorted(self.mem.keys(), reverse=True)
        for addr in addrs:
            val    = self.mem[addr]
            offset = addr - self.RBP if self.RBP else 0
            off_s  = f"RBP{offset:+d}" if self.RBP else "—"
            marker = ""
            if addr == self.RSP: marker += " ←RSP"
            if addr == self.RBP: marker += " ←RBP"
            note   = (highlight or {}).get(addr, "")
            print(f"  0x{addr:010X}  0x{val:016X}  {off_s:>10}  {note}{marker}")
        print()


# ── 模擬 1：基本函式呼叫與返回 ───────────────────────────────

def demo_basic_call():
    print("=" * 65)
    print("  示範 1：基本函式呼叫（CALL / RET）")
    print("=" * 65)

    print("""
  C 程式碼：
    int add(int a, int b) { return a + b; }
    int main() { int r = add(10, 20); }

  對應組語流程：
""")

    s = Stack()
    regs = {'RDI': 0, 'RSI': 0, 'RAX': 0, 'RBP': 0}

    def show_regs(step: str):
        print(f"  [{step}]")
        print(f"    RSP=0x{s.RSP:010X}  RBP=0x{regs['RBP']:010X}  "
              f"RDI={regs['RDI']}  RSI={regs['RSI']}  RAX={regs['RAX']}")

    RETURN_ADDR = 0x0040_1010   # 假設的返回位址（CALL 後的下一條指令）

    print("  ── 呼叫者（main）──────────────────────────────")
    regs['RDI'] = 10
    regs['RSI'] = 20
    show_regs("MOV RDI,10  MOV RSI,20")

    # CALL add：壓入返回位址，跳入函式
    s.push(RETURN_ADDR, "返回位址")
    show_regs(f"CALL add  （壓入返回位址 0x{RETURN_ADDR:X}）")
    s.show("CALL 後的堆疊", {s.RSP: "返回位址（RIP+5）"})

    print("  ── 被呼叫者（add）─ 序言 ─────────────────────")
    # PUSH RBP
    regs['RBP_saved'] = regs['RBP']
    s.push(regs['RBP'], "舊 RBP")
    # MOV RBP, RSP
    regs['RBP'] = s.RSP
    s.RBP = s.RSP
    show_regs("PUSH RBP  MOV RBP,RSP")
    s.show("序言後的堆疊", {
        s.RSP:     "舊 RBP  [RBP+0]",
        s.RSP + 8: "返回位址 [RBP+8]",
    })

    print("  ── 函式主體 ────────────────────────────────────")
    regs['RAX'] = regs['RDI'] + regs['RSI']
    show_regs(f"MOV EAX,EDI  ADD EAX,ESI  →  RAX={regs['RAX']}")

    print("  ── 結語 ────────────────────────────────────────")
    # POP RBP
    regs['RBP'] = s.pop()
    s.RBP = regs['RBP']
    # RET：彈出返回位址
    ret_addr = s.pop()
    show_regs(f"POP RBP  RET  →  跳回 0x{ret_addr:X}")
    print(f"  返回值：RAX = {regs['RAX']}  （= 10 + 20）{'✓' if regs['RAX']==30 else '✗'}")


# ── 模擬 2：區域變數與堆疊對齊 ───────────────────────────────

def demo_local_vars():
    print("\n" + "=" * 65)
    print("  示範 2：區域變數的堆疊佈局")
    print("=" * 65)

    print("""
  C 程式碼：
    int compute(int a, int b) {
        int local_x = a * 2;      // [RBP-4]
        int local_y = b + 10;     // [RBP-8]
        int local_z = local_x + local_y;  // [RBP-12]
        return local_z;
    }
    compute(5, 7)
""")

    s = Stack()
    regs = {'RDI': 5, 'RSI': 7, 'RAX': 0}
    RETURN_ADDR = 0x0040_2020

    # CALL
    s.push(RETURN_ADDR)
    # 序言
    old_rbp = 0x7FFF_1000
    s.push(old_rbp)
    s.RBP = s.RSP
    rbp = s.RSP

    # SUB RSP, 16（3 個 int = 12 bytes，padding 到 16）
    s.sub_rsp(16)

    # 寫入區域變數
    local_x = regs['RDI'] * 2          # 10
    local_y = regs['RSI'] + 10         # 17
    local_z = local_x + local_y        # 27

    s.write(rbp - 4,  local_x)
    s.write(rbp - 8,  local_y)
    s.write(rbp - 12, local_z)

    highlight = {
        s.RSP:      "← RSP（對齊後）",
        rbp - 12:   f"local_z = {local_z}  [RBP-12]",
        rbp - 8:    f"local_y = {local_y}  [RBP-8]",
        rbp - 4:    f"local_x = {local_x}  [RBP-4]",
        rbp:        "舊 RBP           [RBP+0]",
        rbp + 8:    "返回位址         [RBP+8]",
    }
    s.show("函式主體執行後的堆疊", highlight)

    print(f"  存取方式：")
    print(f"    local_x = [RBP-4]  = {s.read(rbp-4)}")
    print(f"    local_y = [RBP-8]  = {s.read(rbp-8)}")
    print(f"    local_z = [RBP-12] = {s.read(rbp-12)}")

    regs['RAX'] = local_z
    print(f"\n  回傳值：RAX = {regs['RAX']}  {'✓' if regs['RAX']==27 else '✗'}")

    # 結語
    s.add_rsp(16)
    s.RBP = s.pop()
    ret = s.pop()
    print(f"  LEAVE + RET：跳回 0x{ret:X}")


# ── 模擬 3：多於 6 個參數的傳遞 ──────────────────────────────

def demo_many_params():
    print("\n" + "=" * 65)
    print("  示範 3：超過 6 個參數的傳遞")
    print("=" * 65)

    print("""
  C 程式碼：
    long sum7(long a, long b, long c, long d,
              long e, long f, long g) {
        return a+b+c+d+e+f+g;
    }
    sum7(1, 2, 3, 4, 5, 6, 7)
""")

    s = Stack()
    params = [1, 2, 3, 4, 5, 6, 7]
    param_regs = ['RDI','RSI','RDX','RCX','R8 ','R9 ']

    print("  呼叫者的操作順序：")

    # 第 7 個以上的參數，由右到左壓堆疊
    print(f"    PUSH {params[6]}          ; 第 7 個參數 g（先壓）")
    s.push(params[6])

    # 前 6 個用暫存器
    for i, (p, reg) in enumerate(zip(params[:6], param_regs)):
        print(f"    MOV {reg}, {p}        ; 第 {i+1} 個參數")

    # CALL
    RETURN_ADDR = 0x0040_3030
    print(f"    CALL sum7")
    s.push(RETURN_ADDR)

    # 序言
    s.push(0x7FFF_2000)   # 舊 RBP
    s.RBP = s.RSP
    rbp = s.RSP

    highlight = {
        rbp:      "舊 RBP            [RBP+0]",
        rbp + 8:  "返回位址          [RBP+8]",
        rbp + 16: f"g = {params[6]}（第7個參數）[RBP+16]",
    }
    s.show("進入 sum7 後的堆疊", highlight)

    print(f"  函式內存取第 7 個參數：")
    g_val = s.read(rbp + 16)
    print(f"    MOV RAX, [RBP+16]  ; RAX = g = {g_val}")
    result = sum(params)
    print(f"\n  計算結果：sum7(1..7) = {result}  {'✓' if result==28 else '✗'}")

    # 結語
    s.RBP = s.pop()
    s.pop()   # 返回位址
    # 呼叫者清除堆疊上的參數
    s.add_rsp(8)
    print(f"  呼叫者執行 ADD RSP, 8  清除堆疊上的 g")


# ── 模擬 4：callee-saved 暫存器保存 ──────────────────────────

def demo_callee_saved():
    print("\n" + "=" * 65)
    print("  示範 4：callee-saved 暫存器的保存與還原")
    print("=" * 65)

    print("""
  規則：
    Callee-saved（被呼叫者保存）：RBX, RBP, R12, R13, R14, R15
    函式若使用這些暫存器，必須在使用前 PUSH，返回前以相反順序 POP

  C 等效：
    void heavy_func(long *arr, int n) {
        // 用 RBX 存 arr，R12 存 n，R13 當迴圈計數
        long sum = 0;
        for (int i = 0; i < n; i++) sum += arr[i];
    }
""")

    s = Stack()
    RETURN_ADDR = 0x0040_4040

    # CALL
    s.push(RETURN_ADDR)

    print("  heavy_func 序言：")
    steps = [
        ("PUSH RBP",   "保存 RBP（callee-saved）"),
        ("MOV RBP,RSP","建立堆疊框架"),
        ("PUSH RBX",   "保存 RBX（即將使用）"),
        ("PUSH R12",   "保存 R12（即將使用）"),
        ("PUSH R13",   "保存 R13（即將使用）"),
    ]

    saved_vals = {
        'RBP': 0x7FFF_3000,
        'RBX': 0xAAAA_AAAA_AAAA_AAAA,
        'R12': 0xBBBB_BBBB_BBBB_BBBB,
        'R13': 0xCCCC_CCCC_CCCC_CCCC,
    }

    s.push(saved_vals['RBP'])
    s.RBP = s.RSP
    rbp = s.RSP
    s.push(saved_vals['RBX'])
    s.push(saved_vals['R12'])
    s.push(saved_vals['R13'])

    for step, note in steps:
        print(f"    {step:<20}  ; {note}")

    s.show("序言後（callee-saved 已保存）", {
        rbp + 8:  "返回位址",
        rbp:      "舊 RBP（呼叫者的 RBP）",
        rbp - 8:  "舊 RBX（呼叫者使用的值）",
        rbp - 16: "舊 R12（呼叫者使用的值）",
        rbp - 24: "舊 R13（呼叫者使用的值）",
    })

    print("  函式主體（自由使用 RBX, R12, R13）...")
    print("    MOV RBX, RDI   ; RBX = arr")
    print("    MOV R12, RSI   ; R12 = n")
    print("    XOR R13, R13   ; R13 = 0（迴圈計數）")
    print("    ... 迴圈計算 ...")

    print("\n  heavy_func 結語（必須以相反順序還原）：")
    restore_steps = [
        ("POP R13", saved_vals['R13'], "還原 R13"),
        ("POP R12", saved_vals['R12'], "還原 R12"),
        ("POP RBX", saved_vals['RBX'], "還原 RBX"),
        ("POP RBP", saved_vals['RBP'], "還原 RBP"),
    ]

    all_ok = True
    for step, expected, note in restore_steps:
        restored = s.pop()
        ok = restored == expected
        if not ok: all_ok = False
        print(f"    {step:<10}  ; {note}  "
              f"→ 0x{restored:016X}  {'✓' if ok else '✗'}")

    s.pop()  # 返回位址
    print(f"\n  所有 callee-saved 暫存器還原{'成功 ✓' if all_ok else '失敗 ✗'}")


if __name__ == "__main__":
    demo_basic_call()
    demo_local_vars()
    demo_many_params()
    demo_callee_saved()