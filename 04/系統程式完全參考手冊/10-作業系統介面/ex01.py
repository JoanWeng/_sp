# ============================================================
#  第 10 章　習題 01 — 系統呼叫模擬器
#  實作：模擬 Linux x86-64 系統呼叫的呼叫約定、
#        行程狀態轉換、虛擬記憶體佈局，以及訊號分派流程
# ============================================================

from dataclasses import dataclass, field
from enum import Enum
import random


# ── 10.1 系統呼叫呼叫約定示範 ────────────────────────────────

SYSCALL_TABLE = {
    0:  ("read",        ["fd", "buf", "count"]),
    1:  ("write",       ["fd", "buf", "count"]),
    2:  ("open",        ["path", "flags", "mode"]),
    3:  ("close",       ["fd"]),
    9:  ("mmap",        ["addr", "len", "prot", "flags", "fd", "offset"]),
    10: ("mprotect",    ["addr", "len", "prot"]),
    11: ("munmap",      ["addr", "len"]),
    12: ("brk",         ["addr"]),
    22: ("pipe",        ["pipefd"]),
    39: ("getpid",      []),
    57: ("fork",        []),
    59: ("execve",      ["path", "argv", "envp"]),
    60: ("exit",        ["status"]),
    62: ("kill",        ["pid", "sig"]),
    231:("exit_group",  ["status"]),
}

SIGNAL_TABLE = {
    1:  ("SIGHUP",  "終止"),
    2:  ("SIGINT",  "終止 (Ctrl+C)"),
    3:  ("SIGQUIT", "核心傾印 (Ctrl+\\)"),
    4:  ("SIGILL",  "核心傾印 (非法指令)"),
    6:  ("SIGABRT", "核心傾印 (abort)"),
    8:  ("SIGFPE",  "核心傾印 (除以零 / FPU 錯誤)"),
    9:  ("SIGKILL", "終止 (無法攔截)"),
    11: ("SIGSEGV", "核心傾印 (非法記憶體存取)"),
    13: ("SIGPIPE", "終止 (管道無讀端)"),
    14: ("SIGALRM", "終止 (alarm 計時器)"),
    15: ("SIGTERM", "終止 (優雅終止)"),
    17: ("SIGCHLD", "忽略 (子行程狀態改變)"),
    19: ("SIGSTOP", "暫停 (無法攔截)"),
    20: ("SIGTSTP", "暫停 (Ctrl+Z)"),
}

def demo_syscall_convention():
    print("=" * 65)
    print("  系統呼叫呼叫約定（Linux x86-64）")
    print("=" * 65)

    print("""
  暫存器分配：
    RAX  = 系統呼叫編號
    RDI  = 第 1 個引數
    RSI  = 第 2 個引數
    RDX  = 第 3 個引數
    R10  = 第 4 個引數（注意：不是 RCX！）
    R8   = 第 5 個引數
    R9   = 第 6 個引數

  回傳值：RAX（失敗時為 -errno，如 -2 = ENOENT）
  SYSCALL 指令會破壞 RCX 和 R11。
""")

    arg_regs = ["RDI", "RSI", "RDX", "R10", "R8", "R9"]

    examples = [
        (1,  [1, "msg_addr", 13],                "write(stdout, msg, 13)"),
        (2,  ["path_addr", 0, 0],                "open(path, O_RDONLY)"),
        (9,  [0, 4096, 3, 34, -1, 0],            "mmap(NULL,4096,RW,PRIVATE|ANON,-1,0)"),
        (60, [0],                                 "exit(0)"),
        (57, [],                                  "fork()"),
    ]

    for syscall_num, args, desc in examples:
        name, param_names = SYSCALL_TABLE[syscall_num]
        print(f"  【{desc}】")
        print(f"    MOV RAX, {syscall_num:>3}   ; sys_{name}")
        for i, (reg, val) in enumerate(zip(arg_regs, args)):
            pname = param_names[i] if i < len(param_names) else f"arg{i+1}"
            if isinstance(val, str):
                print(f"    LEA {reg}, [{val}]   ; {pname}")
            elif val == -1:
                print(f"    MOV {reg}, -1    ; {pname} = -1")
            elif val == 0:
                print(f"    XOR {reg}, {reg}   ; {pname} = 0")
            else:
                print(f"    MOV {reg}, {val:<5}   ; {pname} = {val}")
        print(f"    SYSCALL")
        print()


# ── 10.2 行程狀態模擬 ─────────────────────────────────────────

class ProcState(Enum):
    RUNNING  = "RUNNING"
    SLEEPING = "SLEEPING"
    ZOMBIE   = "ZOMBIE"
    STOPPED  = "STOPPED"
    READY    = "READY"

@dataclass
class Process:
    pid:      int
    ppid:     int
    name:     str
    state:    ProcState = ProcState.READY
    exit_code: int      = 0
    children: list      = field(default_factory=list)
    open_fds: set       = field(default_factory=lambda: {0, 1, 2})
    signals:  list      = field(default_factory=list)

class ProcessManager:
    def __init__(self):
        self.processes: dict[int, Process] = {}
        self._next_pid = 1
        self.log: list[str] = []

    def _new_pid(self) -> int:
        pid = self._next_pid
        self._next_pid += 1
        return pid

    def create(self, name: str, ppid: int = 0) -> Process:
        pid = self._new_pid()
        proc = Process(pid=pid, ppid=ppid, name=name)
        self.processes[pid] = proc
        self.log.append(f"  建立行程 {name}（PID={pid}, PPID={ppid}）→ READY")
        return proc

    def fork(self, parent: Process) -> Process:
        child = Process(
            pid=self._new_pid(),
            ppid=parent.pid,
            name=parent.name,
            state=ProcState.READY,
            open_fds=set(parent.open_fds),  # 繼承 fd 表（Copy-on-Write 概念）
        )
        self.processes[child.pid] = child
        parent.children.append(child.pid)
        self.log.append(
            f"  fork(): 父={parent.pid}（{parent.name}）"
            f"→ 子={child.pid}  [繼承 {len(child.open_fds)} 個 fd]")
        return child

    def exec(self, proc: Process, new_name: str):
        old = proc.name
        proc.name = new_name
        proc.state = ProcState.RUNNING
        # exec 後關閉 FD_CLOEXEC 的 fd（簡化：不模擬）
        self.log.append(
            f"  execve(): PID={proc.pid} {old} → {new_name}  [RUNNING]")

    def exit(self, proc: Process, code: int = 0):
        proc.state    = ProcState.ZOMBIE
        proc.exit_code = code
        self.log.append(
            f"  exit({code}): PID={proc.pid}（{proc.name}）→ ZOMBIE"
            f"  [等待父行程 wait()]")

    def wait(self, parent: Process) -> Process | None:
        for cpid in parent.children:
            child = self.processes[cpid]
            if child.state == ProcState.ZOMBIE:
                child.state = ProcState.SLEEPING   # 標記為已回收（簡化）
                parent.children.remove(cpid)
                self.log.append(
                    f"  wait(): 父={parent.pid} 回收子={cpid}（{child.name}）"
                    f"，退出碼={child.exit_code}")
                return child
        return None

    def send_signal(self, sender_pid: int, target: Process, sig: int):
        name, default = SIGNAL_TABLE.get(sig, (f"SIG{sig}", "終止"))
        target.signals.append(sig)
        self.log.append(
            f"  kill({target.pid}, {name}): 來自 PID={sender_pid}，"
            f"預設行為={default}")
        if sig in (9, 15):   # SIGKILL / SIGTERM → 立刻終止
            self.exit(target, -sig)

    def print_table(self):
        print(f"\n  行程表：")
        print(f"  {'PID':>5} {'PPID':>5} {'狀態':<10} {'名稱':<16} {'開啟fd數':>6} {'子行程'}")
        print(f"  {'─'*60}")
        for pid, p in sorted(self.processes.items()):
            children_str = str(p.children) if p.children else "—"
            print(f"  {p.pid:>5} {p.ppid:>5} {p.state.value:<10} {p.name:<16} "
                  f"{len(p.open_fds):>6}   {children_str}")

def demo_process_lifecycle():
    print("\n" + "=" * 65)
    print("  示範 2：行程生命週期（fork / exec / wait / exit）")
    print("=" * 65)

    pm = ProcessManager()

    # 建立 shell
    shell = pm.create("bash", ppid=1)
    shell.state = ProcState.RUNNING

    print(f"""
  模擬：bash 執行 `ls -l` 的 fork-exec 流程

    bash 呼叫 fork()
      → 子行程（bash 的複製）
      → 子行程呼叫 execve("/bin/ls", ["-l"], envp)
      → 子行程變成 ls 行程
    bash 呼叫 wait() 等待 ls 結束
    ls 執行完畢，exit(0)
    bash 繼續
""")

    # fork
    child = pm.fork(shell)
    shell.state = ProcState.SLEEPING  # 父行程 wait 中

    # exec
    pm.exec(child, "ls")

    # ls 結束
    pm.exit(child, 0)

    # bash wait
    pm.wait(shell)
    shell.state = ProcState.RUNNING

    for line in pm.log:
        print(line)

    pm.print_table()

    # 訊號示範
    print(f"\n  訊號示範：傳送 SIGTERM 給 ls（若還在執行）")
    rogue = pm.create("sleep", ppid=shell.pid)
    rogue.state = ProcState.RUNNING
    shell.children.append(rogue.pid)
    pm.send_signal(shell.pid, rogue, 15)   # SIGTERM
    for line in pm.log[-2:]:
        print(line)


# ── 10.3 虛擬記憶體佈局視覺化 ────────────────────────────────

@dataclass
class VMARegion:
    name:   str
    start:  int
    end:    int
    perms:  str         # r/w/x/p
    note:   str = ""

def demo_virtual_memory():
    print("\n" + "=" * 65)
    print("  示範 3：虛擬記憶體佈局（64-bit Linux 行程）")
    print("=" * 65)

    regions = [
        VMARegion("[kernel]",     0xFFFF800000000000, 0xFFFFFFFFFFFFFFFF,
                  "---", "核心空間（使用者不可存取）"),
        VMARegion("[stack]",      0x7FFE0000, 0x7FFFFFFF0000,
                  "rwxp", "函式呼叫堆疊（向下成長）"),
        VMARegion("[vvar/vdso]",  0x7FFFF7FF8000, 0x7FFFF7FFC000,
                  "r--p", "核心的虛擬 DSO（快速系統呼叫）"),
        VMARegion("libc.so",      0x7FFFF7A00000, 0x7FFFF7BC0000,
                  "r-xp", "C 標準函式庫（.text）"),
        VMARegion("libc.so",      0x7FFFF7BC0000, 0x7FFFF7BC5000,
                  "rw-p", "C 標準函式庫（.data/.bss）"),
        VMARegion("[heap]",       0x00602000, 0x00623000,
                  "rw-p", "malloc 管理的動態記憶體（向上成長）"),
        VMARegion(".bss",         0x00601018, 0x00602000,
                  "rw-p", "未初始化全域變數"),
        VMARegion(".data",        0x00601000, 0x00601018,
                  "rw-p", "已初始化全域變數"),
        VMARegion(".rodata",      0x00400E00, 0x00601000,
                  "r--p", "唯讀資料（字串常數等）"),
        VMARegion(".text",        0x00400000, 0x00400E00,
                  "r-xp", "程式碼（可讀 + 可執行）"),
    ]

    print(f"\n  {'區域名稱':<16} {'起始位址':>18} {'結束位址':>18} {'權限':<6} 說明")
    print(f"  {'─'*80}")
    for r in sorted(regions, key=lambda x: x.start, reverse=True):
        size_kb = (r.end - r.start) // 1024
        size_s  = f"({size_kb}KB)" if size_kb < 10000 else "(大)"
        print(f"  {r.name:<16} 0x{r.start:016X} 0x{r.end:016X} "
              f"{r.perms:<6} {r.note} {size_s}")

    print(f"""
  權限說明：
    r = 可讀（Readable）
    w = 可寫（Writable）
    x = 可執行（Executable）
    p = 私有（Private，Copy-on-Write）
    s = 共享（Shared）

  安全機制：
    .text 為 r-xp（唯讀 + 可執行，不可寫）
    .data / stack 為 rw-p（不可執行，防止注入 shellcode）
    ASLR：每次執行時 heap / stack / 程式庫的位址隨機化
""")


# ── 10.4 Page Fault 處理流程示範 ─────────────────────────────

def demo_page_fault():
    print("=" * 65)
    print("  示範 4：Page Fault 處理分類")
    print("=" * 65)

    scenarios = [
        {
            "desc":   "合法 Stack 成長",
            "addr":   0x7FFE_FFFF_FFF0,
            "type":   "存取合法但尚未配置的 Stack 頁面",
            "result": "OS 配置新頁面，更新頁面表 → 繼續執行 ✓",
            "signal": None,
        },
        {
            "desc":   "Copy-on-Write",
            "addr":   0x0060_1000,
            "type":   "寫入 fork 後共享的唯讀頁面",
            "result": "OS 複製頁面給子行程，改為可寫 → 繼續執行 ✓",
            "signal": None,
        },
        {
            "desc":   "Demand Paging（mmap 檔案）",
            "addr":   0x7FFF_F7A0_1000,
            "type":   "首次存取 mmap 的 libc.so 頁面",
            "result": "OS 從磁碟讀入頁面 → 繼續執行 ✓",
            "signal": None,
        },
        {
            "desc":   "NULL pointer dereference",
            "addr":   0x0000_0000_0000_0000,
            "type":   "存取位址 0（未映射）",
            "result": "→ 傳送 SIGSEGV → 程式崩潰 ✗",
            "signal": "SIGSEGV",
        },
        {
            "desc":   "寫入唯讀 .text",
            "addr":   0x0040_1234,
            "type":   "嘗試修改程式碼區段（保護違規）",
            "result": "→ 傳送 SIGSEGV → 程式崩潰 ✗",
            "signal": "SIGSEGV",
        },
        {
            "desc":   "Stack Overflow",
            "addr":   0x7FFD_0000_0000,
            "type":   "Stack 遞迴太深，超出 Stack 限制（8MB）",
            "result": "→ 傳送 SIGSEGV → 程式崩潰 ✗",
            "signal": "SIGSEGV",
        },
    ]

    print(f"\n  Page Fault 發生時，CR2 = 造成錯誤的虛擬位址\n")
    for sc in scenarios:
        icon = "✓" if sc["signal"] is None else "✗"
        print(f"  [{icon}] {sc['desc']}")
        print(f"      虛擬位址：0x{sc['addr']:016X}")
        print(f"      原因：{sc['type']}")
        print(f"      處理：{sc['result']}")
        print()


# ── 10.5 系統呼叫錯誤碼 ──────────────────────────────────────

ERRNO_TABLE = {
    1:  "EPERM   （Operation not permitted）",
    2:  "ENOENT  （No such file or directory）",
    9:  "EBADF   （Bad file descriptor）",
    11: "EAGAIN  （Resource temporarily unavailable）",
    12: "ENOMEM  （Out of memory）",
    13: "EACCES  （Permission denied）",
    14: "EFAULT  （Bad address）",
    17: "EEXIST  （File exists）",
    20: "ENOTDIR （Not a directory）",
    21: "EISDIR  （Is a directory）",
    22: "EINVAL  （Invalid argument）",
    28: "ENOSPC  （No space left on device）",
    32: "EPIPE   （Broken pipe）",
    35: "EDEADLK （Resource deadlock avoided）",
}

def demo_error_handling():
    print("=" * 65)
    print("  示範 5：系統呼叫錯誤處理（errno 機制）")
    print("=" * 65)

    print(f"""
  系統呼叫失敗時：
    核心回傳 RAX = -errno（負值）
    libc 的包裝函式：
      if (RAX < 0):
          errno = -RAX    （設定全域的 errno）
          return -1       （統一回傳 -1）

  組語的錯誤檢查：
    SYSCALL
    TEST  RAX, RAX
    JS    handle_error   ; RAX < 0 → 錯誤
    ; 成功時繼續...

  handle_error:
    NEG   RAX            ; RAX = errno（正值）
    ; 根據 RAX 處理不同錯誤碼
""")

    print(f"  常用 errno 對照表：")
    print(f"  {'errno':>6}  說明")
    print(f"  {'─'*45}")
    for code, desc in sorted(ERRNO_TABLE.items()):
        print(f"  {code:>6}  {desc}")

    print(f"""
  常見系統呼叫的失敗案例：

  open("/nonexistent", O_RDONLY)
    → RAX = -2（-ENOENT）
    → 錯誤：找不到檔案

  write(99, buf, 10)   （fd 99 未開啟）
    → RAX = -9（-EBADF）
    → 錯誤：無效的檔案描述符

  mmap(NULL, 10TB, ...)
    → RAX = -12（-ENOMEM）
    → 錯誤：記憶體不足
""")


if __name__ == "__main__":
    demo_syscall_convention()
    demo_process_lifecycle()
    demo_virtual_memory()
    demo_page_fault()
    demo_error_handling()