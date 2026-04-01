# ============================================================
#  第 5 章　習題 02 — 控制流程與字串指令模擬
#  實作：模擬條件跳躍的決策邏輯、REP 字串指令的執行過程，
#        以及常見的迴圈、if-else、switch 等控制結構
# ============================================================


# ── 條件跳躍模擬 ─────────────────────────────────────────────

def simulate_jmp_table():
    """展示所有條件跳躍指令與對應的旗標條件"""
    print("=" * 65)
    print("  條件跳躍指令全覽（CMP EAX, EBX 後）")
    print("=" * 65)

    print("""
  CMP 的本質是 SUB（不儲存結果）：
    CMP EAX, EBX  →  計算 EAX - EBX，依結果更新旗標
""")

    # 旗標條件函式
    def jcc(name, CF, ZF, SF, OF, PF=0):
        conds = {
            'JE':   ZF == 1,
            'JNE':  ZF == 0,
            'JC':   CF == 1,
            'JNC':  CF == 0,
            'JS':   SF == 1,
            'JNS':  SF == 0,
            'JO':   OF == 1,
            'JNO':  OF == 0,
            'JP':   PF == 1,
            'JNP':  PF == 0,
            # 無號數
            'JA':   CF == 0 and ZF == 0,
            'JAE':  CF == 0,
            'JB':   CF == 1,
            'JBE':  CF == 1 or ZF == 1,
            # 有號數
            'JG':   ZF == 0 and SF == OF,
            'JGE':  SF == OF,
            'JL':   SF != OF,
            'JLE':  ZF == 1 or SF != OF,
        }
        return conds.get(name, False)

    # 四種典型的 CMP 情境
    scenarios = [
        ("EAX = EBX = 10",   0, 1, 0, 0),   # CF=0, ZF=1, SF=0, OF=0
        ("EAX=20 > EBX=10", 0, 0, 0, 0),   # 正數差，無特殊旗標
        ("EAX=5 < EBX=10",  1, 0, 1, 0),   # 借位，差為負
        ("EAX=-1,EBX=1 (unsigned: EAX=4294967295 > EBX=1)",
                             1, 0, 0, 0),   # 有號<，無號>
    ]

    jumps = ['JE','JNE','JG','JGE','JL','JLE','JA','JAE','JB','JBE']

    for desc, CF, ZF, SF, OF in scenarios:
        print(f"\n  【{desc}】  CF={CF} ZF={ZF} SF={SF} OF={OF}")
        print(f"  {'指令':<6}", end="")
        for j in jumps:
            print(f" {j:<5}", end="")
        print()
        print(f"  {'跳？':<6}", end="")
        for j in jumps:
            result = jcc(j, CF, ZF, SF, OF)
            print(f" {'✓':<5}" if result else f" {'×':<5}", end="")
        print()


def simulate_if_else():
    """模擬 if-else 的組語翻譯"""
    print("\n" + "=" * 65)
    print("  if-else 的組語翻譯模擬")
    print("=" * 65)

    print("""
  C 語言：
    if (a > b) {
        result = a - b;
    } else {
        result = b - a;
    }

  對應組語（EAX=a, EBX=b, ECX=result）：

    CMP EAX, EBX          ; 比較 a 與 b
    JLE else_branch        ; a <= b → 跳到 else（條件取反！）
    ; then 分支
    MOV ECX, EAX
    SUB ECX, EBX           ; result = a - b
    JMP end_if
  else_branch:
    MOV ECX, EBX
    SUB ECX, EAX           ; result = b - a
  end_if:

  ★ 注意：跳躍條件是「何時跳過 then 分支」，與 C 的條件相反
""")

    # 實際執行模擬
    test_pairs = [(15, 8), (3, 20), (7, 7)]
    print("  執行結果：")
    for a, b in test_pairs:
        eax, ebx = a, b
        # 模擬 CMP
        diff = eax - ebx
        ZF = int(diff == 0)
        SF = int(diff < 0)
        CF = int(eax < ebx)
        OF = 0   # 簡化
        # JLE: ZF=1 or SF!=OF
        jle = ZF == 1 or SF != OF
        if not jle:   # then 分支
            result = eax - ebx
            branch = "then"
        else:          # else 分支
            result = ebx - eax
            branch = "else"
        print(f"    a={a:3d}, b={b:3d}  → {branch} 分支  result = {result}")


def simulate_switch():
    """模擬 switch 的跳躍表實作"""
    print("\n" + "=" * 65)
    print("  switch 的跳躍表（Jump Table）模擬")
    print("=" * 65)

    print("""
  C 語言：
    switch (key) {
        case 0: action = "zero";  break;
        case 1: action = "one";   break;
        case 2: action = "two";   break;
        case 3: action = "three"; break;
        default: action = "other";
    }

  編譯器通常產生跳躍表（case 密集時）：
    CMP EAX, 3            ; 超出範圍？
    JA  default_case
    JMP [table + EAX*8]   ; 跳到對應 case（間接跳躍）

  跳躍表（每項 8 bytes，存放各 case 的位址）：
    table: DQ case_0, case_1, case_2, case_3
""")

    jump_table = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
    }

    print("  執行模擬：")
    for key in range(6):
        if key > 3:
            action = "other (default)"
            via = "JA default"
        else:
            action = jump_table[key]
            via = f"JMP [table + {key}×8]"
        print(f"    key={key}  →  {via:<22}  action = '{action}'")


# ── 字串指令模擬 ─────────────────────────────────────────────

class StringOpSimulator:
    """模擬 REP 字串指令（MOVSB/STOSB/SCASB/CMPSB）"""

    def __init__(self):
        self.mem  = bytearray(512)
        self.RSI  = 0
        self.RDI  = 256
        self.RCX  = 0
        self.RAX  = 0
        self.DF   = 0    # 0=正向，1=反向
        self.ZF   = 0
        self.steps = []

    def write(self, addr: int, data: bytes):
        self.mem[addr:addr + len(data)] = data

    def read_byte(self, addr: int) -> int:
        return self.mem[addr]

    def _dir(self):
        return -1 if self.DF else 1

    def movsb(self, verbose: bool = True):
        """MOVSB：[RDI] = [RSI]，RSI/RDI 各 ±1"""
        src_val = self.mem[self.RSI]
        self.mem[self.RDI] = src_val
        if verbose:
            self.steps.append(
                f"  MOVSB: [0x{self.RDI:02X}]←[0x{self.RSI:02X}]"
                f"=0x{src_val:02X}('{chr(src_val) if 32<=src_val<127 else '.'}') "
                f"RSI={self.RSI+self._dir():#x} RDI={self.RDI+self._dir():#x}"
            )
        self.RSI += self._dir()
        self.RDI += self._dir()

    def stosb(self, verbose: bool = True):
        """STOSB：[RDI] = AL，RDI ±1"""
        fill = self.RAX & 0xFF
        self.mem[self.RDI] = fill
        if verbose:
            self.steps.append(
                f"  STOSB: [0x{self.RDI:02X}]←AL=0x{fill:02X}  "
                f"RDI={self.RDI+self._dir():#x}"
            )
        self.RDI += self._dir()

    def scasb(self, verbose: bool = True):
        """SCASB：AL - [RDI]，設旗標，RDI ±1"""
        mem_val = self.mem[self.RDI]
        al_val  = self.RAX & 0xFF
        diff    = al_val - mem_val
        self.ZF = int(diff == 0)
        if verbose:
            match = "✓ 找到！" if self.ZF else "✗"
            self.steps.append(
                f"  SCASB: AL(0x{al_val:02X}) vs [0x{self.RDI:02X}]"
                f"(0x{mem_val:02X}='{chr(mem_val) if 32<=mem_val<127 else '.'}') "
                f"ZF={self.ZF} {match}"
            )
        self.RDI += self._dir()

    def rep_movsb(self, count: int):
        self.RCX = count
        self.steps = []
        print(f"\n  REP MOVSB（複製 {count} bytes，RSI→RDI）：")
        print(f"  初始：RSI=0x{self.RSI:02X} RDI=0x{self.RDI:02X}")
        while self.RCX > 0:
            self.movsb()
            self.RCX -= 1
        for s in self.steps:
            print(s)
        print(f"  完成：RSI=0x{self.RSI:02X} RDI=0x{self.RDI:02X} RCX={self.RCX}")

    def rep_stosb(self, count: int, fill_byte: int):
        self.RCX = count
        self.RAX = fill_byte
        self.steps = []
        print(f"\n  REP STOSB（填充 {count} bytes，值=0x{fill_byte:02X}）：")
        print(f"  初始：RDI=0x{self.RDI:02X}")
        while self.RCX > 0:
            self.stosb()
            self.RCX -= 1
        for s in self.steps:
            print(s)
        print(f"  完成：RDI=0x{self.RDI:02X} RCX={self.RCX}")

    def repne_scasb(self, search_byte: int, max_count: int = 64):
        self.RCX = max_count
        self.RAX = search_byte
        self.steps = []
        print(f"\n  REPNE SCASB（搜尋 0x{search_byte:02X}"
              f"='{chr(search_byte) if 32<=search_byte<127 else '?'}'）：")
        start_rdi = self.RDI
        while self.RCX > 0:
            self.scasb()
            self.RCX -= 1
            if self.ZF:   # REPNE：找到（ZF=1）則停止
                break
        for s in self.steps:
            print(s)
        if self.ZF:
            found_at = self.RDI - self._dir() - start_rdi  # 相對偏移
            print(f"  找到！位於偏移 {found_at}（相對搜尋起點）")
        else:
            print(f"  未找到（搜尋 {max_count} bytes 後放棄）")


def demo_rep_instructions():
    print("\n" + "=" * 65)
    print("  REP 字串指令執行模擬")
    print("=" * 65)

    sim = StringOpSimulator()

    # ── 示範 1：REP MOVSB（memcpy）────────────────────────
    print("\n【示範 1】REP MOVSB → memcpy(dst, src, 8)")
    src_data = b"Hello!\n\0"
    sim.RSI = 0
    sim.RDI = 0x20
    sim.write(0, src_data)
    sim.rep_movsb(8)

    # 驗證複製結果
    copied = bytes(sim.mem[0x20:0x28])
    print(f"  驗證：複製結果 = {copied}  {'✓' if copied == src_data else '✗'}")

    # ── 示範 2：REP STOSB（memset）────────────────────────
    print("\n【示範 2】REP STOSB → memset(dst, 0xCC, 6)")
    sim.RDI = 0x40
    sim.rep_stosb(6, 0xCC)
    filled = list(sim.mem[0x40:0x46])
    print(f"  驗證：0x40～0x45 = {[hex(b) for b in filled]}  "
          f"{'✓' if all(b == 0xCC for b in filled) else '✗'}")

    # ── 示範 3：REPNE SCASB（strlen / strchr）──────────────
    print("\n【示範 3】REPNE SCASB → 搜尋 '!' 在字串中的位置")
    test_str = b"Hello World! Test\0"
    sim.write(0x60, test_str)
    sim.RDI = 0x60
    sim.repne_scasb(ord('!'))

    # ── 示範 4：strlen 模擬 ────────────────────────────────
    print("\n【示範 4】strlen 模擬（REPNE SCASB 搜尋 null）")
    test_str2 = b"Assembly\0"
    sim.write(0x80, test_str2)
    sim.RDI = 0x80
    start = sim.RDI

    sim.RAX = 0           # 搜尋 0（null terminator）
    sim.RCX = 0xFFFF      # 最大長度
    sim.steps = []
    while sim.RCX > 0:
        sim.scasb(verbose=False)
        sim.RCX -= 1
        if sim.ZF:
            break

    strlen = sim.RDI - start - 1  # -1 因為已越過 null
    print(f"  字串：\"{test_str2.decode().rstrip(chr(0))}\"")
    print(f"  strlen 結果：{strlen}  {'✓' if strlen == len(test_str2)-1 else '✗'}")


def demo_loop_patterns():
    print("\n" + "=" * 65)
    print("  常見迴圈模式的組語對應")
    print("=" * 65)

    print("""
  ── for 迴圈 ─────────────────────────────────────────
  C：  for (int i = 0; i < 10; i++) { sum += i; }

  組語：
    MOV ECX, 0          ; i = 0
    MOV EAX, 0          ; sum = 0
  .for_loop:
    CMP ECX, 10         ; i < 10?
    JGE .for_end        ; i >= 10 則離開
    ADD EAX, ECX        ; sum += i
    INC ECX             ; i++
    JMP .for_loop
  .for_end:

  ── while 迴圈 ───────────────────────────────────────
  C：  while (n > 1) { if (n%2) n=3*n+1; else n/=2; }

  組語：
  .while_loop:
    CMP EAX, 1          ; n > 1?
    JLE .while_end
    TEST EAX, 1         ; n % 2（測試最低位）
    JZ  .even
  .odd:
    LEA EAX, [EAX+EAX*2+1]   ; n = 3*n + 1（LEA 技巧）
    JMP .while_loop
  .even:
    SHR EAX, 1          ; n /= 2
    JMP .while_loop
  .while_end:

  ── do-while 迴圈 ────────────────────────────────────
  C：  do { sum += arr[i]; i++; } while (i < n);

  組語：
  .do_loop:
    ADD EAX, [arr + ECX*4]   ; sum += arr[i]
    INC ECX                   ; i++
    CMP ECX, EDX              ; i < n?
    JL  .do_loop              ; 是則繼續（條件在尾部）
""")

    # 執行模擬：do-while 計算陣列總和
    arr    = [3, 1, 4, 1, 5, 9, 2, 6]
    EAX    = 0   # sum
    ECX    = 0   # i
    EDX    = len(arr)  # n
    steps  = []

    while True:
        EAX += arr[ECX]
        ECX += 1
        steps.append(f"    i={ECX-1} arr[i]={arr[ECX-1]:2d} sum={EAX}")
        if ECX >= EDX:
            break

    print(f"  do-while 模擬（arr={arr}）：")
    for s in steps:
        print(s)
    print(f"  總和 = {EAX}  {'✓' if EAX == sum(arr) else '✗'}")


if __name__ == "__main__":
    simulate_jmp_table()
    simulate_if_else()
    simulate_switch()
    demo_rep_instructions()
    demo_loop_patterns()