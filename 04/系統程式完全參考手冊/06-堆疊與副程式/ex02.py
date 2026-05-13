# ============================================================
#  第 6 章　習題 02 — 遞迴函式的堆疊展開視覺化
#  實作：視覺化 factorial / fibonacci / hanoi 的遞迴呼叫樹
#        與堆疊框架的建立和釋放過程
# ============================================================

import sys
sys.setrecursionlimit(500)


# ── 遞迴追蹤工具 ─────────────────────────────────────────────

class RecursionTracer:
    """記錄遞迴呼叫的堆疊狀態"""

    def __init__(self):
        self.call_stack  = []   # 目前的呼叫鏈
        self.max_depth   = 0
        self.total_calls = 0
        self.log         = []

    def enter(self, func: str, args: str, frame_size: int = 32):
        self.total_calls += 1
        depth = len(self.call_stack)
        self.max_depth = max(self.max_depth, depth + 1)
        frame = {
            'func':       func,
            'args':       args,
            'depth':      depth,
            'frame_size': frame_size,
            'rsp_offset': -(depth + 1) * frame_size,
        }
        self.call_stack.append(frame)
        indent = "  " + "│  " * depth + "├─ "
        self.log.append(f"{indent}CALL {func}({args})"
                        f"  [RSP{frame['rsp_offset']:+d}]")
        return frame

    def leave(self, result):
        frame = self.call_stack.pop()
        depth = len(self.call_stack)
        indent = "  " + "│  " * depth + "└→ "
        self.log.append(f"{indent}RET  {frame['func']} = {result}")
        return frame

    def print_log(self, title: str):
        print(f"\n  {'─'*3} {title} {'─'*(45-len(title))}")
        for line in self.log:
            print(line)
        print(f"\n  統計：最大遞迴深度 = {self.max_depth}，"
              f"總呼叫次數 = {self.total_calls}")

    def print_stack_at_peak(self, func: str, base_rsp: int = 0x7FFF_0000,
                            frame_size: int = 32):
        print(f"\n  最深堆疊時的框架佈局（{func}，深度 {self.max_depth}）：")
        print(f"  {'位址':>12}  {'框架歸屬':<25}  {'RSP 偏移':>10}")
        print(f"  {'─'*55}")
        for i in range(self.max_depth, 0, -1):
            addr = base_rsp - i * frame_size
            owner = f"  {func}（第 {i} 層）"
            offset = -(self.max_depth - i + 1) * frame_size
            marker = " ←RSP" if i == self.max_depth else ""
            print(f"  0x{addr:08X}  {owner:<25}  {offset:>+10}{marker}")
        total_used = self.max_depth * frame_size
        print(f"\n  堆疊使用量：{self.max_depth} 層 × {frame_size} bytes"
              f" = {total_used} bytes")


# ── 階乘（Factorial）────────────────────────────────────────

def demo_factorial():
    print("=" * 65)
    print("  遞迴 1：階乘（Factorial）")
    print("=" * 65)

    print("""
  C 程式碼：
    long factorial(long n) {
        if (n <= 1) return 1;
        return n * factorial(n - 1);
    }

  對應組語（簡化）：
    factorial:
        PUSH RBP; MOV RBP,RSP; PUSH RBX   ; 序言（32B 框架）
        CMP  RDI, 1
        JLE  .base
        MOV  RBX, RDI          ; RBX = n
        DEC  RDI
        CALL factorial          ; 遞迴
        IMUL RAX, RBX          ; n × factorial(n-1)
        JMP  .done
    .base: MOV RAX, 1
    .done: POP RBX; POP RBP; RET
""")

    tracer = RecursionTracer()

    def factorial(n: int) -> int:
        tracer.enter("factorial", f"n={n}")
        if n <= 1:
            result = 1
        else:
            sub = factorial(n - 1)
            result = n * sub
        tracer.leave(result)
        return result

    N = 5
    result = factorial(N)
    tracer.print_log(f"factorial({N}) 的遞迴呼叫樹")
    tracer.print_stack_at_peak("factorial")
    print(f"\n  factorial({N}) = {result}  {'✓' if result==120 else '✗'}")


# ── 費波那契（Fibonacci）─────────────────────────────────────

def demo_fibonacci():
    print("\n" + "=" * 65)
    print("  遞迴 2：費波那契數列（Fibonacci）")
    print("=" * 65)

    print("""
  C 程式碼：
    long fib(long n) {
        if (n <= 1) return n;
        return fib(n-1) + fib(n-2);
    }

  注意：fib(n) 有兩個遞迴呼叫，呼叫次數爆炸性增長！
    fib(5) 共呼叫 15 次
    fib(10) 共呼叫 177 次
    fib(30) 共呼叫 2,692,537 次
""")

    tracer = RecursionTracer()

    def fib(n: int) -> int:
        tracer.enter("fib", f"n={n}")
        if n <= 1:
            result = n
        else:
            a = fib(n - 1)
            b = fib(n - 2)
            result = a + b
        tracer.leave(result)
        return result

    N = 5
    result = fib(N)
    tracer.print_log(f"fib({N}) 的遞迴呼叫樹")
    tracer.print_stack_at_peak("fib")
    print(f"\n  fib({N}) = {result}  {'✓' if result==5 else '✗'}")

    print("\n  fib 的呼叫次數比較：")
    print(f"  {'n':>4}  {'呼叫次數':>10}  {'結果':>8}")
    print(f"  {'─'*30}")

    def fib_count(n):
        if n <= 1: return n, 1
        r1, c1 = fib_count(n-1)
        r2, c2 = fib_count(n-2)
        return r1+r2, c1+c2+1

    for n in [1, 3, 5, 7, 10]:
        val, cnt = fib_count(n)
        print(f"  {n:>4}  {cnt:>10}  {val:>8}")


# ── 尾遞迴最佳化示範 ─────────────────────────────────────────

def demo_tail_recursion():
    print("\n" + "=" * 65)
    print("  示範 3：尾遞迴最佳化（Tail Call Optimization）")
    print("=" * 65)

    print("""
  普通遞迴（不可最佳化）：
    long factorial(long n) {
        if (n <= 1) return 1;
        return n * factorial(n-1);  // 還需要 ×n，不是尾呼叫
    }

  尾遞迴版本（可最佳化）：
    long factorial_tail(long n, long acc) {
        if (n <= 1) return acc;
        return factorial_tail(n-1, acc*n);  // 最後只做呼叫，是尾呼叫
    }

  組語最佳化（尾呼叫轉為 JMP，不建立新框架）：
    factorial_tail:
        PUSH RBP; MOV RBP,RSP
    .loop:                       ; ← 把函式入口當迴圈起點
        CMP  RDI, 1
        JLE  .base
        IMUL RSI, RDI            ; acc = acc × n
        DEC  RDI                 ; n = n - 1
        JMP  .loop               ; ← JMP 而非 CALL，重用框架！
    .base:
        MOV  RAX, RSI
        POP  RBP
        RET
""")

    # 普通遞迴的堆疊使用
    tracer_normal = RecursionTracer()

    def factorial_normal(n):
        tracer_normal.enter("factorial", f"n={n}")
        result = 1 if n <= 1 else n * factorial_normal(n - 1)
        tracer_normal.leave(result)
        return result

    # 尾遞迴（模擬最佳化後只用 1 個框架）
    tracer_tail = RecursionTracer()

    def factorial_tail(n, acc=1):
        # 最佳化後等同迴圈，不計入遞迴深度
        while n > 1:
            acc *= n
            n -= 1
        tracer_tail.enter("factorial_tail", f"n={n},acc={acc}")
        tracer_tail.leave(acc)
        return acc

    N = 6
    r1 = factorial_normal(N)
    r2 = factorial_tail(N)

    print(f"  factorial({N}) 比較：")
    print(f"  {'版本':<20}  {'最大深度':>8}  {'總呼叫次數':>10}  {'堆疊用量':>12}")
    print(f"  {'─'*56}")
    print(f"  {'普通遞迴':<20}  "
          f"{tracer_normal.max_depth:>8}  "
          f"{tracer_normal.total_calls:>10}  "
          f"{tracer_normal.max_depth * 32:>10} bytes")
    print(f"  {'尾遞迴（最佳化後）':<20}  "
          f"{'1':>8}  "
          f"{'1':>10}  "
          f"{'32':>10} bytes")
    print(f"\n  結果驗證：{r1} == {r2}  {'✓' if r1==r2 else '✗'}")
    print(f"  堆疊節省：{tracer_normal.max_depth}x → 1x"
          f"（節省 {(tracer_normal.max_depth-1)*32} bytes）")


# ── 漢諾塔（Tower of Hanoi）─────────────────────────────────

def demo_hanoi():
    print("\n" + "=" * 65)
    print("  示範 4：漢諾塔（Tower of Hanoi）遞迴步驟")
    print("=" * 65)

    print("""
  漢諾塔規則：
    將 n 個圓盤從 A 柱移到 C 柱（以 B 柱為中繼）
    每次只能移一個，且大圓盤不能疊在小圓盤上

  遞迴公式：
    hanoi(n, A, C, B):
        if n == 1: 移動 A→C
        else:
            hanoi(n-1, A, B, C)  // 把 n-1 個移到中繼柱
            移動 A→C             // 移動最大的
            hanoi(n-1, B, C, A)  // 把 n-1 個從中繼柱移到目的
""")

    moves = []
    tracer = RecursionTracer()

    def hanoi(n: int, src: str, dst: str, mid: str, depth: int = 0):
        tracer.enter("hanoi", f"n={n},{src}→{dst}")
        if n == 1:
            moves.append(f"  移動圓盤 {n}：{src} → {dst}")
        else:
            hanoi(n - 1, src, mid, dst, depth + 1)
            moves.append(f"  移動圓盤 {n}：{src} → {dst}")
            hanoi(n - 1, mid, dst, src, depth + 1)
        tracer.leave(None)

    N = 3
    hanoi(N, 'A', 'C', 'B')

    tracer.print_log(f"hanoi({N}) 的遞迴呼叫樹")

    print(f"\n  移動步驟（共 {len(moves)} 步，= 2^{N}-1 = {2**N-1}）：")
    for i, m in enumerate(moves, 1):
        print(f"  {i:>3}.{m}")

    tracer.print_stack_at_peak("hanoi")


if __name__ == "__main__":
    demo_factorial()
    demo_fibonacci()
    demo_tail_recursion()
    demo_hanoi()