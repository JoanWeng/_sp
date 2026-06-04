# ============================================================
#  第 12 章　習題 01 — 開發工具模擬器
#  實作：模擬 GCC 編譯管線、Makefile 相依分析、
#        objdump 反組譯輸出，以及 strace 系統呼叫追蹤
# ============================================================

import os
import re
from dataclasses import dataclass, field
from typing import Optional


# ══════════════════════════════════════════════════════════════
#  示範 1：GCC 編譯管線模擬
# ══════════════════════════════════════════════════════════════

def demo_gcc_pipeline():
    print("=" * 65)
    print("  示範 1：GCC 四階段編譯管線")
    print("=" * 65)

    source = """\
#include <stdio.h>

#define GREETING "Hello, World!"

int main(void) {
    printf(GREETING "\\n");
    return 0;
}"""

    stages = [
        {
            "stage": "① 前置處理（Preprocessing）",
            "cmd":   "gcc -E hello.c -o hello.i",
            "input": "hello.c（含 #include / #define）",
            "output": "hello.i（展開後的純 C 程式碼）",
            "desc": """\
  展開結果（簡化）：
    # 1 "hello.c"
    # 1 "<built-in>"
    ... （stdio.h 展開，約 700+ 行）...
    int main(void) {
        printf("Hello, World!" "\\n");  ← #define 已替換
        return 0;
    }""",
        },
        {
            "stage": "② 編譯（Compilation）",
            "cmd":   "gcc -S hello.i -o hello.s",
            "input": "hello.i（純 C 程式碼）",
            "output": "hello.s（AT&T 組合語言）",
            "desc": """\
  AT&T 組語輸出（簡化）：
    .LC0:
        .string "Hello, World!\\n"
    main:
        pushq   %rbp
        movq    %rsp, %rbp
        leaq    .LC0(%rip), %rax
        movq    %rax, %rdi
        call    puts@PLT          ← printf 被最佳化成 puts
        movl    $0, %eax
        popq    %rbp
        ret

  注意：GCC 預設輸出 AT&T 語法（暫存器加 %，立即值加 $）
  若想看 Intel 語法：gcc -S -masm=intel hello.c""",
        },
        {
            "stage": "③ 組譯（Assembly）",
            "cmd":   "gcc -c hello.s -o hello.o",
            "input": "hello.s（組合語言）",
            "output": "hello.o（可重定位 ELF 目的碼）",
            "desc": """\
  目的碼特性：
    - ELF 格式，type = ET_REL（可重定位）
    - 含符號表（main、puts 為 UNDEF）
    - 含重定位表（puts@PLT 的呼叫位址待填）
    - 絕對位址尚未確定（LC = 0x0000 開始）

  驗證：
    file hello.o
    → ELF 64-bit LSB relocatable, x86-64
    readelf -s hello.o
    → 可看到 puts: UNDEF GLOBAL""",
        },
        {
            "stage": "④ 連結（Linking）",
            "cmd":   "gcc hello.o -o hello",
            "input": "hello.o（+ libc.so / crt0.o）",
            "output": "hello（可執行 ELF）",
            "desc": """\
  連結器完成：
    - 符號解析：puts → libc.so 中的 puts
    - 重定位：填入 puts@PLT 的正確位址
    - 加入 crt0（C runtime：呼叫 __libc_start_main → main）
    - 加入 PLT / GOT（動態連結存根）
    - 設定 ELF 進入點（e_entry = _start）

  驗證：
    file hello
    → ELF 64-bit LSB pie executable
    ldd hello
    → libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6""",
        },
    ]

    print(f"\n  原始碼 hello.c：")
    for line in source.splitlines():
        print(f"    {line}")

    for s in stages:
        print(f"\n  {'─'*60}")
        print(f"  {s['stage']}")
        print(f"  指令：{s['cmd']}")
        print(f"  輸入：{s['input']}")
        print(f"  輸出：{s['output']}")
        print(s['desc'])


# ══════════════════════════════════════════════════════════════
#  示範 2：Makefile 相依圖分析
# ══════════════════════════════════════════════════════════════

@dataclass
class MakeTarget:
    name:  str
    deps:  list[str] = field(default_factory=list)
    cmds:  list[str] = field(default_factory=list)
    mtime: float     = 0.0   # 模擬修改時間

class MakeSimulator:
    def __init__(self):
        self.targets: dict[str, MakeTarget] = {}
        self.files:   dict[str, float]      = {}   # 檔案 → 修改時間
        self.build_log: list[str]           = []
        self._time = 1.0

    def add_target(self, name: str, deps: list[str], cmds: list[str]):
        self.targets[name] = MakeTarget(name, deps, cmds)

    def touch(self, filename: str, time: float = None):
        if time is None:
            self._time += 1
            time = self._time
        self.files[filename] = time

    def _needs_rebuild(self, target: str) -> bool:
        """判斷目標是否需要重建（目標不存在 or 任何依賴比目標新）"""
        if target not in self.files and target not in self.targets:
            return False  # 非目標也非檔案（可能是外部依賴）
        if target not in self.files:
            return True   # 目標不存在
        t_time = self.files.get(target, 0)
        for dep in self.targets.get(target, MakeTarget(target)).deps:
            dep_time = self.files.get(dep, 0)
            if dep_time > t_time:
                return True
        return False

    def make(self, target: str, visited: set = None) -> bool:
        """遞迴建置目標，回傳是否實際執行了建置"""
        if visited is None:
            visited = set()
        if target in visited:
            self.build_log.append(f"  ⚠ 循環依賴偵測：{target}")
            return False
        visited.add(target)

        t = self.targets.get(target)
        if not t:
            # 純檔案依賴，不是目標
            return False

        # 先遞迴建置所有依賴
        any_rebuilt = False
        for dep in t.deps:
            if dep in self.targets:
                rebuilt = self.make(dep, visited)
                if rebuilt:
                    any_rebuilt = True

        # 判斷是否需要重建本目標
        if self._needs_rebuild(target) or any_rebuilt:
            self.build_log.append(f"\n  建置：{target}")
            for cmd in t.cmds:
                self.build_log.append(f"    $ {cmd}")
            self._time += 1
            self.files[target] = self._time   # 更新 mtime
            return True
        else:
            self.build_log.append(f"  跳過（最新）：{target}")
            return False


def demo_makefile():
    print("\n" + "=" * 65)
    print("  示範 2：Makefile 相依分析與增量建置")
    print("=" * 65)

    mk = MakeSimulator()

    # 定義 Makefile 規則
    mk.add_target("all",     ["myapp"], [])
    mk.add_target("myapp",   ["main.o", "util.o", "asm.o"],
                  ["gcc -o myapp main.o util.o asm.o"])
    mk.add_target("main.o",  ["main.c", "util.h"],
                  ["gcc -c main.c -o main.o"])
    mk.add_target("util.o",  ["util.c", "util.h"],
                  ["gcc -c util.c -o util.o"])
    mk.add_target("asm.o",   ["asm.asm"],
                  ["nasm -f elf64 asm.asm -o asm.o"])

    # 初始化所有原始檔（時間較舊）
    for f, t in [("main.c", 1.0), ("util.c", 1.0), ("util.h", 1.0),
                 ("asm.asm", 1.0)]:
        mk.touch(f, t)

    print("\n  【第一次建置（從零開始）】")
    mk.make("all")
    for log in mk.build_log:
        print(log)

    # 清空 log
    mk.build_log = []

    print("\n  【第二次 make（無任何改動）】")
    mk.make("all")
    for log in mk.build_log:
        print(log)

    mk.build_log = []

    # 修改 util.h（會影響 main.o 和 util.o）
    print("\n  【修改 util.h 後的增量建置】")
    mk.touch("util.h")   # util.h 變新了
    mk.make("all")
    for log in mk.build_log:
        print(log)

    print(f"""
  增量建置說明：
    修改 util.h → main.o 和 util.o 都需要重建（因為它們依賴 util.h）
    asm.o 不依賴 util.h → 跳過（節省時間）
    myapp 依賴的 main.o 和 util.o 被重建 → myapp 也需要重新連結
""")

    # 依賴圖
    print("  相依關係圖：")
    print("    all")
    print("     └── myapp")
    print("          ├── main.o ← main.c, util.h")
    print("          ├── util.o ← util.c, util.h")
    print("          └── asm.o  ← asm.asm")


# ══════════════════════════════════════════════════════════════
#  示範 3：模擬 objdump 列表輸出
# ══════════════════════════════════════════════════════════════

def demo_objdump():
    print("=" * 65)
    print("  示範 3：objdump -d -M intel 的輸出格式")
    print("=" * 65)

    print("""
  指令：objdump -d -M intel hello
  格式：位址：機器碼（hex bytes）    助記符  運算元
""")

    # 模擬一段真實的 objdump 輸出
    listing = [
        ("",        "",                         "0000000000401000 <_start>:"),
        ("401000",  "b8 01 00 00 00",           "mov    eax,0x1"),
        ("401005",  "bf 01 00 00 00",           "mov    edi,0x1"),
        ("40100a",  "48 8d 35 ef 0f 00 00",     "lea    rsi,[rip+0xfef]        # 402000 <msg>"),
        ("401011",  "ba 0e 00 00 00",           "mov    edx,0xe"),
        ("401016",  "0f 05",                    "syscall"),
        ("401018",  "b8 3c 00 00 00",           "mov    eax,0x3c"),
        ("40101d",  "31 ff",                    "xor    edi,edi"),
        ("40101f",  "0f 05",                    "syscall"),
        ("",        "",                         ""),
        ("",        "",                         "0000000000401021 <helper>:"),
        ("401021",  "55",                       "push   rbp"),
        ("401022",  "48 89 e5",                 "mov    rbp,rsp"),
        ("401025",  "89 7d fc",                 "mov    DWORD PTR [rbp-0x4],edi"),
        ("401028",  "8b 45 fc",                 "mov    eax,DWORD PTR [rbp-0x4]"),
        ("40102b",  "83 c0 01",                 "add    eax,0x1"),
        ("40102e",  "5d",                       "pop    rbp"),
        ("40102f",  "c3",                       "ret"),
    ]

    for addr, bytes_hex, asm in listing:
        if not addr:
            print(f"  {asm}")
        else:
            print(f"  {addr}:  {bytes_hex:<26}  {asm}")

    print(f"""
  重點解讀：
    · RIP 相對定址：lea rsi,[rip+0xfef]
      RIP = 下一條指令位址 = 0x401011
      msg = 0x401011 + 0xfef = 0x402000 ✓

    · syscall（0F 05）= 2 bytes
    · push rbp（55）  = 1 byte
    · mov rbp,rsp（48 89 e5）= 3 bytes（含 REX prefix 0x48）

  常用 objdump 選項：
    -d           反組譯 .text
    -S           混合原始碼（需要 -g 編譯）
    -M intel     Intel 語法（目的地在左）
    -r           顯示重定位表
    -t           顯示符號表
""")


# ══════════════════════════════════════════════════════════════
#  示範 4：strace 系統呼叫追蹤模擬
# ══════════════════════════════════════════════════════════════

def demo_strace():
    print("=" * 65)
    print("  示範 4：strace 系統呼叫追蹤（Hello World）")
    print("=" * 65)

    print("""
  指令：strace ./hello
  格式：syscall_name(args...) = return_value

  以下是 ./hello 執行時的完整系統呼叫序列：
""")

    strace_output = [
        ("execve",     '"./hello", ["./hello"], 0x7ffe... /* 20 vars */',   "0"),
        ("brk",        "NULL",                                               "0x55a1c2e01000"),
        ("arch_prctl", "0x3001 /* ARCH_??? */, 0x7ffd...",                  "-1 EINVAL"),
        ("mmap",       "NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0",
                       "0x7f3a4b200000"),
        ("access",     '"/etc/ld.so.preload", R_OK',                        "-1 ENOENT"),
        ("openat",     'AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC', "3"),
        ("newfstatat", "3, \"\", {st_mode=..., st_size=...}, AT_EMPTY_PATH","0"),
        ("mmap",       "NULL, 186033, PROT_READ, MAP_PRIVATE, 3, 0",        "0x7f3a4b1d0000"),
        ("close",      "3",                                                  "0"),
        ("openat",     'AT_FDCWD, "/lib/x86_64-linux-gnu/libc.so.6", O_RDONLY|O_CLOEXEC', "3"),
        ("read",       "3, \"\\177ELF\\2\\1\\1\\3\\0...\"..., 832",         "832"),
        ("mmap",       "NULL, 1966080, PROT_READ, MAP_PRIVATE|MAP_DENYWRITE, 3, 0",
                       "0x7f3a4b000000"),
        ("...",        "（載入 libc.so 的其他 mmap 呼叫）",                  "..."),
        ("close",      "3",                                                  "0"),
        ("mprotect",   "0x7f3a4b034000, 1474560, PROT_NONE",                "0"),
        ("mmap",       "0x7f3a4b034000, 1196032, PROT_READ|PROT_EXEC...",   "0x7f3a4b034000"),
        ("arch_prctl", "ARCH_SET_FS, 0x7f3a4b201740",                       "0"),
        ("write",      '1, "Hello, World!\\n", 14',                         "14"),
        ("exit_group", "0",                                                  "?"),
    ]

    print(f"  {'系統呼叫':<12}  {'引數（截短）':<52}  = 回傳值")
    print(f"  {'─'*80}")
    for syscall, args, ret in strace_output:
        args_short = args[:50] + "..." if len(args) > 50 else args
        print(f"  {syscall:<12}({args_short})")
        print(f"  {'':14}= {ret}")

    print(f"""
  關鍵觀察：
    1. execve() 是第一個系統呼叫（核心啟動程式）
    2. 大量 mmap/openat → 動態連結器載入 libc.so
    3. arch_prctl(ARCH_SET_FS) → 設定 TLS（Thread Local Storage）
    4. write(1, ..., 14) → 我們程式碼實際的輸出
    5. exit_group(0)     → 程式結束
    6. 中間有很多「隱藏」的初始化工作（libc 啟動）

  strace -c ./hello 的統計輸出：
  % time   seconds  usecs/call  calls syscall
  ─────────────────────────────────────────────
   71.43   0.000005          5      1 write
   14.29   0.000001          1     12 mmap
    7.14   0.000001          1      3 openat
    ...
""")


# ══════════════════════════════════════════════════════════════
#  示範 5：GDB 指令速查卡
# ══════════════════════════════════════════════════════════════

def demo_gdb_cheatsheet():
    print("=" * 65)
    print("  示範 5：GDB 常用指令速查")
    print("=" * 65)

    categories = [
        ("中斷點", [
            ("break main",          "在 main 函式設中斷點"),
            ("break *0x401000",     "在位址設中斷點（組語用）"),
            ("watch x",             "當 x 的值改變時停止"),
            ("info breakpoints",    "列出所有中斷點"),
            ("delete 1",            "刪除中斷點 #1"),
        ]),
        ("執行控制", [
            ("run / r",             "開始執行"),
            ("continue / c",        "繼續到下一個中斷點"),
            ("next / n",            "下一行（不進入函式）"),
            ("step / s",            "下一行（進入函式）"),
            ("finish",              "執行到目前函式結束"),
            ("stepi / si",          "一條機器指令"),
            ("nexti / ni",          "一條機器指令（不進入）"),
        ]),
        ("檢視狀態", [
            ("print x",             "印出變數 x"),
            ("print/x $rax",        "以 hex 印出 RAX 暫存器"),
            ("info registers",      "顯示所有暫存器"),
            ("x/10x $rsp",          "以 hex 顯示 RSP 後 10 個 word"),
            ("x/10i $rip",          "反組譯 RIP 後 10 條指令"),
            ("x/s 0x601000",        "以字串顯示記憶體"),
            ("backtrace / bt",      "顯示呼叫堆疊"),
            ("info locals",         "顯示目前框架的區域變數"),
        ]),
        ("設定", [
            ("set disassembly-flavor intel", "切換為 Intel 語法"),
            ("set print pretty on",          "美化結構體輸出"),
            ("layout asm",                   "TUI：顯示組語視窗"),
            ("layout regs",                  "TUI：顯示暫存器"),
            ("layout split",                 "TUI：原始碼+組語"),
        ]),
    ]

    for cat, cmds in categories:
        print(f"\n  ── {cat} ────────────────────────────────────")
        for cmd, desc in cmds:
            print(f"  (gdb) {cmd:<40}  # {desc}")

    print(f"""
  典型除錯流程：
    $ gcc -g -O0 program.c -o program
    $ gdb -tui ./program
    (gdb) set disassembly-flavor intel
    (gdb) break main
    (gdb) run
    (gdb) layout split        ← 同時看原始碼和組語
    (gdb) next                ← 逐行執行
    (gdb) print variable      ← 查看變數值
    (gdb) backtrace           ← 崩潰時查看呼叫堆疊
""")


if __name__ == "__main__":
    demo_gcc_pipeline()
    demo_makefile()
    demo_objdump()
    demo_strace()
    demo_gdb_cheatsheet()