# ============================================================
#  第 6 章　習題 03 — 堆疊平衡檢查器與呼叫慣例驗證
#  實作：自動驗證多層巢狀函式呼叫的堆疊平衡，
#        模擬 printf 等變長引數函式的呼叫慣例，
#        以及 Stack Canary 保護機制的運作原理
# ============================================================

import random
import struct


# ── 堆疊平衡檢查器 ───────────────────────────────────────────

class StackBalanceChecker:
    """
    模擬一連串的 PUSH/POP/CALL/RET 操作，
    自動偵測堆疊不平衡的情形
    """

    def __init__(self, base_rsp: int = 0x7FFF_0000):
        self.base_rsp  = base_rsp
        self.RSP       = base_rsp
        self.call_stack = []   # 儲存每個 CALL 時的 RSP
        self.ops        = []
        self.errors     = []

    def _log(self, op: str, rsp_before: int, ok: bool = True):
        rsp_delta = self.RSP - rsp_before
        sign = '+' if rsp_delta >= 0 else ''
        self.ops.append({
            'op':        op,
            'rsp_after': self.RSP,
            'delta':     rsp_delta,
            'ok':        ok,
        })

    def push(self, label: str = ""):
        before = self.RSP
        self.RSP -= 8
        self._log(f"PUSH {label}", before)

    def pop(self, label: str = ""):
        before = self.RSP
        self.RSP += 8
        self._log(f"POP  {label}", before)

    def sub_rsp(self, n: int, label: str = ""):
        before = self.RSP
        self.RSP -= n
        self._log(f"SUB RSP, {n}  ({label})", before)

    def add_rsp(self, n: int, label: str = ""):
        before = self.RSP
        self.RSP += n
        self._log(f"ADD RSP, {n}  ({label})", before)

    def call(self, func_name: str):
        before = self.RSP
        self.call_stack.append((func_name, self.RSP))
        self.RSP -= 8   # CALL 壓入返回位址
        self._log(f"CALL {func_name}", before)

    def ret(self):
        before = self.RSP
        self.RSP += 8   # RET 彈出返回位址

        if not self.call_stack:
            self.errors.append("❌ RET 但 call_stack 為空！")
            self._log("RET（錯誤！）", before, ok=False)
            return

        func_name, expected_rsp = self.call_stack.pop()
        if self.RSP != expected_rsp:
            err = (f"❌ {func_name} 返回後 RSP=0x{self.RSP:08X}，"
                   f"預期 0x{expected_rsp:08X}（差 {self.RSP - expected_rsp} bytes）")
            self.errors.append(err)
            self._log(f"RET {func_name}（堆疊不平衡！）", before, ok=False)
        else:
            self._log(f"RET {func_name} ✓", before)

    def report(self):
        print(f"\n  {'操作':<35}  {'RSP 後':>12}  {'Δ':>6}  狀態")
        print(f"  {'─'*65}")
        for op_info in self.ops:
            status = "✓" if op_info['ok'] else "❌"
            delta  = op_info['delta']
            dsign  = '+' if delta >= 0 else ''
            print(f"  {op_info['op']:<35}  "
                  f"0x{op_info['rsp_after']:08X}  "
                  f"{dsign}{delta:>4}  {status}")

        final_delta = self.RSP - self.base_rsp
        print(f"\n  最終 RSP = 0x{self.RSP:08X}（初始 + {final_delta}）")
        if final_delta == 0 and not self.errors:
            print(f"  ✅ 堆疊平衡！所有 PUSH/POP/CALL/RET 已正確配對。")
        else:
            print(f"  ❌ 堆疊不平衡（差 {final_delta} bytes）")
            for e in self.errors:
                print(f"  {e}")


def demo_stack_balance():
    print("=" * 65)
    print("  示範 1：堆疊平衡檢查（正確案例）")
    print("=" * 65)

    print("""
  模擬以下呼叫序列：
    main() → func_a() → func_b()
""")

    c = StackBalanceChecker()

    # main 的序言
    c.push("RBP（main）")
    c.sub_rsp(16, "main 區域變數")

    # 呼叫 func_a
    c.call("func_a")
    # func_a 序言
    c.push("RBP（func_a）")
    c.sub_rsp(32, "func_a 區域變數")
    # func_a 呼叫 func_b
    c.call("func_b")
    # func_b 序言
    c.push("RBP（func_b）")
    # func_b 結語
    c.pop("RBP（func_b）")
    c.ret()
    # func_a 結語
    c.add_rsp(32, "還原 func_a 區域變數")
    c.pop("RBP（func_a）")
    c.ret()

    # main 結語
    c.add_rsp(16, "還原 main 區域變數")
    c.pop("RBP（main）")

    c.report()

    # ── 錯誤案例 ──────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  示範 2：堆疊不平衡偵測（錯誤案例）")
    print("=" * 65)

    print("""
  模擬錯誤：func_bad 忘記 POP RBP 就 RET
""")

    c2 = StackBalanceChecker()
    c2.push("RBP（caller）")
    c2.call("func_bad")
    c2.push("RBP（func_bad）")
    c2.sub_rsp(16, "func_bad 區域變數")
    # ❌ 忘記 ADD RSP, 16 和 POP RBP
    c2.ret()   # RSP 未還原就 RET！
    c2.pop("RBP（caller）")
    c2.report()


# ── 變長引數函式呼叫模擬 ─────────────────────────────────────

class VariadicCallSimulator:
    """模擬 printf 等變長引數函式的呼叫慣例"""

    def __init__(self):
        self.int_regs  = ['RDI', 'RSI', 'RDX', 'RCX', 'R8', 'R9']
        self.xmm_regs  = [f'XMM{i}' for i in range(8)]
        self.stack_args = []

    def setup_call(self, args: list) -> dict:
        """
        依 System V AMD64 ABI 分配參數。
        args: list of (type, value)，type 為 'int'/'float'/'ptr'

        回傳：暫存器分配字典與 EAX 值（XMM 使用數量）
        """
        int_idx  = 0
        xmm_idx  = 0
        reg_map  = {}
        stack    = []

        for arg_type, val in args:
            if arg_type in ('int', 'ptr', 'long'):
                if int_idx < len(self.int_regs):
                    reg_map[self.int_regs[int_idx]] = (arg_type, val)
                    int_idx += 1
                else:
                    stack.append((arg_type, val))
            elif arg_type in ('float', 'double'):
                if xmm_idx < len(self.xmm_regs):
                    reg_map[self.xmm_regs[xmm_idx]] = (arg_type, val)
                    xmm_idx += 1
                else:
                    stack.append((arg_type, val))

        return {
            'reg_map':  reg_map,
            'stack':    stack,
            'eax':      xmm_idx,  # XMM 使用數量（變長引數函式需要）
        }

    def show_call(self, func_name: str, args: list):
        result = self.setup_call(args)
        print(f"\n  呼叫：{func_name}({', '.join(f'{v}({t})' for t,v in args)})")
        print(f"\n  暫存器分配：")
        for reg, (t, v) in result['reg_map'].items():
            print(f"    {reg:<6} = {v}  （{t}）")
        if result['stack']:
            print(f"\n  堆疊參數（由右到左壓入）：")
            for i, (t, v) in enumerate(reversed(result['stack']), 1):
                print(f"    第 {len(result['stack'])-i+1} 個堆疊參數：{v}（{t}）")
        print(f"\n  EAX（XMM 使用數量） = {result['eax']}"
              f"  {'← 變長引數函式必須設定！' if result['eax']>0 else ''}")
        return result


def demo_variadic():
    print("\n" + "=" * 65)
    print("  示範 3：變長引數函式（printf）的呼叫慣例")
    print("=" * 65)

    sim = VariadicCallSimulator()

    # 範例 1：printf("%d\n", 42)
    sim.show_call('printf', [
        ('ptr', '"格式字串位址"'),
        ('int', 42),
    ])

    # 範例 2：printf("%d %f %s\n", 10, 3.14, str_ptr)
    sim.show_call('printf', [
        ('ptr',    '"格式字串位址"'),
        ('int',    10),
        ('double', 3.14),
        ('ptr',    '"hello"位址'),
    ])

    # 範例 3：7 個參數（第 7 個進堆疊）
    sim.show_call('func7', [
        ('int', 1), ('int', 2), ('int', 3),
        ('int', 4), ('int', 5), ('int', 6),
        ('int', 7),   # → 堆疊
    ])

    print("""
  ★ 關鍵提醒：呼叫 printf 等變長引數函式時，
    必須在 CALL 前設定 EAX = 使用的 XMM 暫存器數量
    （無浮點參數時 EAX = 0，否則 EAX = XMM 使用數）

  組語範例：
    ; printf("%d\\n", 42)
    lea  rdi, [fmt]     ; 格式字串
    mov  esi, 42        ; 整數參數
    xor  eax, eax       ; ← 無浮點參數，EAX = 0
    call printf

    ; printf("%f\\n", 3.14)
    lea  rdi, [fmt_f]
    movsd xmm0, [pi]    ; 浮點參數放 XMM0
    mov  eax, 1         ; ← 使用了 1 個 XMM 暫存器
    call printf
""")


# ── Stack Canary 模擬 ─────────────────────────────────────────

def demo_stack_canary():
    print("=" * 65)
    print("  示範 4：Stack Canary 保護機制")
    print("=" * 65)

    print("""
  Stack Canary 原理：
    1. 函式序言在返回位址與區域變數之間放置一個隨機值（金絲雀）
    2. 函式結語在 RET 前驗證金絲雀是否被修改
    3. 若緩衝區溢位覆蓋了返回位址，金絲雀必然被覆蓋
    4. 驗證失敗 → 呼叫 __stack_chk_fail → 程式終止

  記憶體佈局（有 Canary）：
    [RBP+8]  返回位址
    [RBP+0]  舊 RBP
    [RBP-8]  ★ Canary 值（隨機）
    [RBP-24] buf[16]（16 bytes 緩衝區）
    [RSP]    ↑ RSP
""")

    # 生成 Canary 值
    canary = random.randint(0x0001_0000_0000_0000, 0xFFFE_FFFF_FFFF_FFFF)
    # Canary 的最低 byte 通常是 0x00（防止字串函式讀過頭）
    canary = (canary & 0xFFFF_FFFF_FFFF_FF00)

    print(f"  ─── 正常函式呼叫（無緩衝區溢位）───────────────")
    buf    = bytearray(16)
    mem    = bytearray(40)  # buf(16) + padding(8) + canary(8) + rbp(8) = 40
    # 寫入 Canary
    struct.pack_into('<Q', mem, 24, canary)   # buf 後 8 bytes 的 canary
    # 寫入正常資料
    safe_input = b"Hello World!"
    mem[:len(safe_input)] = safe_input

    print(f"  輸入：'{safe_input.decode()}'（{len(safe_input)} bytes，安全）")
    print(f"  Canary 值：0x{canary:016X}")
    # 讀回 Canary
    stored = struct.unpack_from('<Q', mem, 24)[0]
    intact = stored == canary
    print(f"  驗證結果：Canary {'完整 ✅' if intact else '被破壞 ❌'}")

    print(f"\n  ─── 緩衝區溢位攻擊（覆蓋 Canary）────────────")
    mem2   = bytearray(40)
    struct.pack_into('<Q', mem2, 24, canary)
    # 惡意輸入：超過 buf 的大小，覆蓋 Canary
    evil_input = b"A" * 32   # 超出 buf[16]，覆蓋到 Canary 位置
    mem2[:min(len(evil_input), 40)] = evil_input[:40]

    print(f"  輸入：'A' × {len(evil_input)} bytes（溢位！）")
    stored2 = struct.unpack_from('<Q', mem2, 24)[0]
    intact2 = stored2 == canary
    print(f"  Canary 期望：0x{canary:016X}")
    print(f"  Canary 實際：0x{stored2:016X}")
    print(f"  驗證結果：Canary {'完整' if intact2 else '被破壞 ❌ → 呼叫 __stack_chk_fail！'}")

    print("""
  對應的組語（GCC 產生）：
    ; 序言：儲存 Canary
    mov  rax, QWORD [fs:0x28]     ; 讀取執行緒專屬的隨機 Canary
    mov  QWORD [rbp-8], rax       ; 存到堆疊

    ; 結語：驗證 Canary
    mov  rax, QWORD [rbp-8]
    xor  rax, QWORD [fs:0x28]     ; 比較（應為 0）
    je   .ok
    call __stack_chk_fail          ; 驗證失敗，終止程式
  .ok:
    leave
    ret
""")


if __name__ == "__main__":
    demo_stack_balance()
    demo_variadic()
    demo_stack_canary()