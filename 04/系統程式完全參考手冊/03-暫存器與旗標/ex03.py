# ============================================================
#  第 3 章　習題 03 — 堆疊框架與暫存器保存模擬
#  實作：模擬函式呼叫時 RSP/RBP 的變化、堆疊框架建立，
#        以及 callee-saved 暫存器的保存與還原流程
# ============================================================


class Stack:
    """模擬 x86-64 堆疊（向低位址成長）"""

    def __init__(self, base_addr: int = 0x7FFF0000, size: int = 256):
        self.mem    = {}                   # 以位址為 key 的記憶體字典
        self.RSP    = base_addr            # 初始 RSP（堆疊底部）
        self.RBP    = 0                    # 基底指標
        self.base   = base_addr
        self.log    = []                   # 操作記錄

    def push(self, value: int, label: str = ""):
        """PUSH：RSP -= 8，然後 [RSP] = value"""
        self.RSP -= 8
        self.mem[self.RSP] = value
        desc = f"PUSH  {label or hex(value):>20}   → [0x{self.RSP:08X}] = 0x{value:016X}"
        self.log.append(desc)
        print(f"  {desc}   RSP=0x{self.RSP:08X}")

    def pop(self, reg_name: str = "?") -> int:
        """POP：value = [RSP]，然後 RSP += 8"""
        value = self.mem.get(self.RSP, 0)
        del self.mem[self.RSP]
        desc = f"POP   {reg_name:>20}   ← [0x{self.RSP:08X}] = 0x{value:016X}"
        self.log.append(desc)
        print(f"  {desc}   RSP=0x{self.RSP + 8:08X}→0x{self.RSP:08X}", end="")
        self.RSP += 8
        print(f"→0x{self.RSP:08X}")
        return value

    def sub_rsp(self, n: int, label: str = ""):
        """SUB RSP, n：為區域變數保留空間"""
        self.RSP -= n
        desc = f"SUB RSP, {n}  (保留 {label or '區域變數'} 空間)"
        self.log.append(desc)
        print(f"  {desc:45}  RSP=0x{self.RSP:08X}")

    def write(self, offset: int, value: int, label: str = ""):
        """MOV [RBP + offset], value"""
        addr = self.RBP + offset
        self.mem[addr] = value
        print(f"  MOV [RBP{offset:+d}], {value:10} = 0x{value:016X}  ; {label}")

    def read(self, offset: int) -> int:
        addr = self.RBP + offset
        return self.mem.get(addr, 0)

    def show_frame(self):
        """顯示目前的堆疊內容"""
        print(f"\n  堆疊快照（RSP=0x{self.RSP:08X}，RBP=0x{self.RBP:08X}）：")
        print(f"  {'位址':>12}  {'值（hex）':>18}  {'偏移（RBP）':>12}  說明")
        print("  " + "-" * 65)

        addrs = sorted(self.mem.keys())
        for addr in addrs:
            val     = self.mem[addr]
            offset  = addr - self.RBP if self.RBP else 0
            marker  = ""
            if addr == self.RSP:
                marker = " ← RSP"
            if addr == self.RBP:
                marker = " ← RBP"
            off_str = f"RBP{offset:+d}" if self.RBP else "—"
            print(f"  0x{addr:08X}   0x{val:016X}   {off_str:>12}  {marker}")
        print()


# ── 模擬一次完整的函式呼叫 ────────────────────────────────────

def simulate_function_call():
    print("=" * 65)
    print("  模擬 C 函式呼叫的堆疊框架建立與銷毀")
    print("=" * 65)

    # 對應的 C 程式碼：
    # int add_and_save(int a, int b) {
    #     int local_x = a + b;
    #     int local_y = local_x * 2;
    #     return local_y;
    # }
    # 呼叫：add_and_save(10, 20)

    stack = Stack()

    # ── 模擬呼叫者（caller）傳遞參數 ────────────────────────
    print("\n【步驟 1】呼叫者傳遞參數（System V AMD64 ABI）")
    # 參數 a=10 → RDI，b=20 → RSI（暫存器傳遞，不壓堆疊）
    RDI = 10   # 第 1 個參數
    RSI = 20   # 第 2 個參數
    print(f"  mov rdi, {RDI}  ; 第 1 個參數 a")
    print(f"  mov rsi, {RSI}  ; 第 2 個參數 b")

    # ── CALL：壓入返回位址 ────────────────────────────────────
    print("\n【步驟 2】CALL 指令（壓入返回位址，RIP+5）")
    return_addr = 0x0040105F   # 假設的返回位址
    stack.push(return_addr, "返回位址（RIP+5）")

    # ── 函式序言（Function Prologue）────────────────────────
    print("\n【步驟 3】函式序言（Prologue）")
    print("  push rbp           ; 保存呼叫者的 RBP")
    stack.push(0x00007FFFFFFF0000, "舊 RBP（呼叫者）")

    print(f"  mov rbp, rsp       ; 設定本函式的 RBP = RSP = 0x{stack.RSP:08X}")
    stack.RBP = stack.RSP

    # 保留兩個 int 的空間（各 4 bytes，但為了 16-byte 對齊，保留 16 bytes）
    print("  sub rsp, 16        ; 保留 16 bytes 給 local_x 和 local_y")
    stack.sub_rsp(16, "local_x(4B) + local_y(4B) + padding(8B)")

    stack.show_frame()

    # ── 函式主體 ─────────────────────────────────────────────
    print("【步驟 4】函式主體執行")

    # local_x = a + b = 10 + 20 = 30
    local_x = RDI + RSI
    print(f"\n  ; local_x = a + b = {RDI} + {RSI} = {local_x}")
    print(f"  mov eax, edi           ; EAX = a = {RDI}")
    print(f"  add eax, esi           ; EAX = EAX + b = {local_x}")
    stack.write(-4, local_x, f"local_x = {local_x}")

    # local_y = local_x * 2 = 60
    local_y = local_x * 2
    print(f"\n  ; local_y = local_x * 2 = {local_x} * 2 = {local_y}")
    print(f"  mov eax, [rbp-4]       ; EAX = local_x = {local_x}")
    print(f"  lea eax, [eax + eax]   ; EAX = EAX * 2 = {local_y}")
    stack.write(-8, local_y, f"local_y = {local_y}")

    stack.show_frame()

    # ── 函式結語（Function Epilogue）────────────────────────
    print("【步驟 5】函式結語（Epilogue）")

    print(f"\n  ; 設定回傳值")
    print(f"  mov eax, [rbp-8]       ; EAX = local_y = {local_y}（回傳值）")
    RAX = local_y

    print(f"\n  ; 銷毀堆疊框架")
    print(f"  mov rsp, rbp           ; RSP = RBP（釋放區域變數）")
    stack.RSP = stack.RBP

    print(f"  pop rbp                ; 還原呼叫者的 RBP")
    old_rbp = stack.pop("RBP")
    stack.RBP = old_rbp

    print(f"\n  ret                    ; 從堆疊彈出返回位址，跳回呼叫者")
    ret_addr = stack.pop("RIP（返回位址）")

    print(f"\n  最終狀態：")
    print(f"    RSP = 0x{stack.RSP:08X}（已還原到呼叫前的位置）")
    print(f"    RAX = {RAX}（回傳值）")
    print(f"    跳回位址：0x{ret_addr:08X}")
    stack.show_frame()


# ── 模擬 Callee-saved 暫存器保存 ─────────────────────────────

def simulate_callee_saved():
    print("\n" + "=" * 65)
    print("  Callee-saved 暫存器的保存與還原")
    print("=" * 65)

    print("""
  Callee-saved 暫存器：RBX, RBP, R12, R13, R14, R15
  規則：若函式要使用這些暫存器，必須在開頭 PUSH，結尾 POP

  範例函式：使用 RBX 和 R12 進行計算
""")

    stack = Stack()

    print("func_heavy:")
    print("  ; 函式序言")
    stack.push(0xCAFEBABECAFEBABE, "舊 RBP")
    stack.RBP = stack.RSP
    print(f"  mov rbp, rsp")

    print("\n  ; 保存 callee-saved 暫存器（若要使用）")
    RBX_saved = 0x1111111111111111   # 模擬呼叫者存在 RBX 的值
    R12_saved = 0x2222222222222222   # 模擬呼叫者存在 R12 的值
    stack.push(RBX_saved, "舊 RBX（呼叫者的值）")
    stack.push(R12_saved, "舊 R12（呼叫者的值）")

    print("\n  ; 現在可以自由使用 RBX 和 R12")
    print(f"  mov rbx, 100    ; RBX 現在屬於本函式")
    print(f"  mov r12, 200    ; R12 現在屬於本函式")
    print(f"  ; ... 執行各種運算 ...")

    print("\n  ; 函式結語：必須以相反順序 POP（LIFO）")
    r12_restored = stack.pop("R12")
    rbx_restored = stack.pop("RBX")
    stack.pop("RBP")

    print(f"\n  ret")
    print(f"\n  還原驗證：")
    print(f"    RBX 還原為 0x{rbx_restored:016X}  "
          f"{'✓' if rbx_restored == RBX_saved else '✗'}")
    print(f"    R12 還原為 0x{r12_restored:016X}  "
          f"{'✓' if r12_restored == R12_saved else '✗'}")


# ── 模擬 RSP 在 PUSH/POP 過程中的變化 ────────────────────────

def demo_rsp_movement():
    print("\n" + "=" * 65)
    print("  RSP（堆疊指標）的移動規律")
    print("=" * 65)

    print("""
  x86-64 堆疊特性：
    · 堆疊向低位址成長
    · PUSH：RSP -= 8，然後寫入 [RSP]
    · POP ：讀取 [RSP]，然後 RSP += 8
    · 初始 RSP 通常在高位址（如 0x7FFFFFFFE000）
""")

    BASE = 0x1000
    RSP  = BASE

    ops = [
        ("PUSH RAX（值=0xAAAA）",  "push", 0xAAAA),
        ("PUSH RBX（值=0xBBBB）",  "push", 0xBBBB),
        ("PUSH RCX（值=0xCCCC）",  "push", 0xCCCC),
        ("POP  RCX",               "pop",  None),
        ("POP  RBX",               "pop",  None),
        ("POP  RAX",               "pop",  None),
    ]

    mem = {}
    print(f"  {'指令':<25} {'RSP 前':>12} {'RSP 後':>12} {'[RSP] 值':>12}")
    print("  " + "-" * 65)

    for desc, op, val in ops:
        rsp_before = RSP
        if op == "push":
            RSP -= 8
            mem[RSP] = val
            stored = val
        else:
            stored = mem.get(RSP, 0)
            del mem[RSP]
            RSP += 8
        rsp_after = RSP
        print(f"  {desc:<25} 0x{rsp_before:08X}   0x{rsp_after:08X}   "
              f"{'0x'+format(stored,'016X') if stored is not None else '—':>18}")

    print(f"\n  最終 RSP = 0x{RSP:08X}（與初始值相同，表示堆疊已平衡 ✓）")
    assert RSP == BASE, "堆疊不平衡！"


if __name__ == "__main__":
    simulate_function_call()
    simulate_callee_saved()
    demo_rsp_movement()