# ============================================================
#  第 8 章　習題 01 — 完整兩遍組譯器模擬
#  實作：Pass1 建立 SYMTAB、Pass2 翻譯指令並產生重定位表，
#        最後輸出模擬的 ELF 目的碼資訊
# ============================================================

from dataclasses import dataclass, field
from enum import Enum


# ── 資料型別定義 ──────────────────────────────────────────────

class SymBind(Enum):
    LOCAL  = "LOCAL"
    GLOBAL = "GLOBAL"
    EXTERN = "EXTERN"   # UNDEF

class SymType(Enum):
    NOTYPE   = "NOTYPE"
    FUNC     = "FUNC"
    OBJECT   = "OBJECT"
    CONSTANT = "CONSTANT"

@dataclass
class Symbol:
    name:    str
    value:   int        # 位址或常數值
    section: str        # ".text" / ".data" / "ABS" / "UNDEF"
    bind:    SymBind    = SymBind.LOCAL
    stype:   SymType    = SymType.NOTYPE
    size:    int        = 0

@dataclass
class Relocation:
    section: str        # 在哪個區段
    offset:  int        # 在區段內的偏移
    symbol:  str        # 引用的符號名稱
    rtype:   str        # 重定位類型
    addend:  int = 0


# ── 簡化的指令長度表 ─────────────────────────────────────────

OPTAB = {
    # 助記符（大寫）: (opcode_bytes, total_length)
    # 僅列出本模擬用到的指令
    'NOP':     (b'\x90',          1),
    'RET':     (b'\xC3',          1),
    'HLT':     (b'\xF4',          1),
    'SYSCALL': (b'\x0F\x05',      2),
    'PUSH':    (None,             2),   # PUSH r64：REX + 50+rd
    'POP':     (None,             2),   # POP  r64：REX + 58+rd
    'INC':     (None,             3),   # INC  r32：FF /0
    'DEC':     (None,             3),
    'NOT':     (None,             3),
    'NEG':     (None,             3),
    'ADD':     (None,             3),   # ADD r,r：ModRM
    'SUB':     (None,             3),
    'XOR':     (None,             3),
    'CMP':     (None,             3),
    'TEST':    (None,             3),
    'MOV_RR':  (None,             3),   # MOV r,r
    'MOV_RI32':(None,             7),   # MOV r64, imm32（REX + B8 + imm32）
    'MOV_RI64':(None,            10),   # MOV r64, imm64（REX + B8 + imm64）
    'MOV_RM':  (None,             7),   # MOV r,[mem]（REX + 8B + ModRM + disp32）
    'LEA':     (None,             7),   # LEA r,[mem]（REX + 8D + ModRM + disp32）
    'CALL':    (b'\xE8',          5),   # CALL rel32
    'JMP_S':   (b'\xEB',          2),   # JMP short
    'JMP_N':   (b'\xE9',          5),   # JMP near
    'JZ_S':    (b'\x74',          2),
    'JNZ_S':   (b'\x75',          2),
    'JZ_N':    (b'\x0F\x84',      6),
    'JNZ_N':   (b'\x0F\x85',      6),
    'JG_N':    (b'\x0F\x8F',      6),
    'JL_N':    (b'\x0F\x8C',      6),
    'JGE_N':   (b'\x0F\x8D',      6),
    'JLE_N':   (b'\x0F\x8E',      6),
}

# 推斷指令長度（簡化，忽略所有運算元細節）
def infer_length(mnemonic: str, operands: str) -> int:
    m = mnemonic.upper()
    ops = operands.strip()

    if m in ('NOP', 'RET', 'HLT'):             return 1
    if m == 'SYSCALL':                          return 2
    if m in ('PUSH', 'POP'):                    return 2
    if m == 'CALL':                             return 5
    if m == 'JMP':
        return 2 if 'SHORT' in ops.upper() else 5
    if m in ('JZ','JE'):
        return 2 if 'SHORT' in ops.upper() else 6
    if m in ('JNZ','JNE'):
        return 2 if 'SHORT' in ops.upper() else 6
    if m in ('JG','JGE','JL','JLE','JA','JB','JAE','JBE'):
        return 6
    if m == 'MOV':
        # 粗略判斷
        if 'RAX' in ops or 'RBX' in ops or 'RCX' in ops or 'RDX' in ops:
            if any(c.isdigit() for c in ops.split(',')[-1].strip()[:3]):
                return 7    # MOV r64, imm32
            return 3        # MOV r64, r64
        return 5
    if m == 'LEA':          return 7
    if m in ('ADD','SUB','XOR','AND','OR','CMP','TEST'): return 3
    if m in ('INC','DEC','NEG','NOT'):                   return 3
    if m == 'IMUL':         return 7
    return 4   # 預設


# ── 組譯器主體 ────────────────────────────────────────────────

class Assembler:

    def __init__(self):
        self.symtab:  dict[str, Symbol]  = {}
        self.reltab:  list[Relocation]   = []
        self.sections = {
            '.text': bytearray(),
            '.data': bytearray(),
            '.bss':  0,             # .bss 只記大小
        }
        self.lc     = {'.text': 0, '.data': 0, '.bss': 0}
        self.cur_sec = '.text'
        self.listing = []    # (原始行, LC, 長度, 注記)

    # ── Pass 1 ────────────────────────────────────────────────

    def pass1(self, source: str):
        """掃描原始碼，建立符號表"""
        lines = source.strip().splitlines()
        for raw in lines:
            line = raw.strip()
            # 去掉行尾註解
            if ';' in line:
                line = line[:line.index(';')].strip()
            if not line:
                continue

            # 處理 section 切換
            if line.lower().startswith('section'):
                sec = line.split()[1].lower()
                if sec in self.lc:
                    self.cur_sec = sec
                continue

            # 處理 global / extern
            if line.lower().startswith('global'):
                name = line.split()[1]
                if name in self.symtab:
                    self.symtab[name].bind = SymBind.GLOBAL
                else:
                    self.symtab[name] = Symbol(
                        name=name, value=0, section='UNDEF',
                        bind=SymBind.GLOBAL)
                continue

            if line.lower().startswith('extern'):
                name = line.split()[1]
                self.symtab[name] = Symbol(
                    name=name, value=0, section='UNDEF',
                    bind=SymBind.EXTERN)
                continue

            # 解析標號
            label = None
            if ':' in line:
                parts = line.split(':', 1)
                label = parts[0].strip()
                line  = parts[1].strip()
                # 記錄到 SYMTAB
                if label in self.symtab and self.symtab[label].section != 'UNDEF':
                    print(f"  ❌ 錯誤：符號 '{label}' 重複定義！")
                else:
                    sym = Symbol(
                        name=label,
                        value=self.lc[self.cur_sec],
                        section=self.cur_sec,
                        bind=SymBind.LOCAL,
                    )
                    # 若之前有 global 宣告，保留 GLOBAL
                    if label in self.symtab and self.symtab[label].bind == SymBind.GLOBAL:
                        sym.bind = SymBind.GLOBAL
                    self.symtab[label] = sym

            if not line:
                continue

            # 計算指令/資料長度，更新 LC
            tokens   = line.split(None, 1)
            mnemonic = tokens[0].upper()
            operands = tokens[1] if len(tokens) > 1 else ''

            if mnemonic in ('DB', 'BYTE'):
                size = self._calc_db_size(operands)
                self.lc[self.cur_sec] += size
            elif mnemonic == 'DW':
                count = len(operands.split(','))
                self.lc[self.cur_sec] += count * 2
            elif mnemonic == 'DD':
                count = len(operands.split(','))
                self.lc[self.cur_sec] += count * 4
            elif mnemonic == 'DQ':
                count = len(operands.split(','))
                self.lc[self.cur_sec] += count * 8
            elif mnemonic == 'RESB':
                n = int(operands.strip())
                self.lc[self.cur_sec] += n
            elif mnemonic == 'RESD':
                n = int(operands.strip())
                self.lc[self.cur_sec] += n * 4
            elif mnemonic == 'EQU':
                # 常數：不改 LC，直接記錄
                val = self._eval_const(operands)
                if label:
                    self.symtab[label] = Symbol(
                        name=label, value=val, section='ABS',
                        bind=SymBind.LOCAL, stype=SymType.CONSTANT)
            else:
                # 機器指令
                size = infer_length(mnemonic, operands)
                self.lc[self.cur_sec] += size

    def _calc_db_size(self, operands: str) -> int:
        total = 0
        for part in operands.split(','):
            p = part.strip()
            if p.startswith('"') or p.startswith("'"):
                inner = p[1:-1]
                total += len(inner.encode('ascii', errors='replace'))
            else:
                total += 1
        return total

    def _eval_const(self, expr: str) -> int:
        try:
            return int(eval(expr.replace('$', '0')))
        except Exception:
            return 0

    # ── Pass 2 ────────────────────────────────────────────────

    def pass2(self, source: str):
        """翻譯指令，產生（假）目的碼和重定位表"""
        lines    = source.strip().splitlines()
        self.cur_sec = '.text'
        lc = {'.text': 0, '.data': 0, '.bss': 0}

        for raw in lines:
            line = raw.strip()
            if ';' in line:
                line = line[:line.index(';')].strip()
            if not line:
                continue

            if line.lower().startswith('section'):
                sec = line.split()[1].lower()
                if sec in lc:
                    self.cur_sec = sec
                continue

            if line.lower().startswith(('global','extern','align')):
                continue

            label = None
            if ':' in line:
                parts = line.split(':', 1)
                label = parts[0].strip()
                line  = parts[1].strip()

            if not line:
                self.listing.append((raw.rstrip(), lc[self.cur_sec],
                                     0, f'標號 {label}' if label else ''))
                continue

            tokens   = line.split(None, 1)
            mnemonic = tokens[0].upper()
            operands = tokens[1] if len(tokens) > 1 else ''
            sec      = self.cur_sec
            addr     = lc[sec]

            if mnemonic in ('DB','DW','DD','DQ','RESB','RESD','EQU'):
                size = self._data_directive(mnemonic, operands, sec, addr, lc)
                note = f'資料定義 ({size}B)'
            else:
                size = infer_length(mnemonic, operands)
                note = self._check_reloc(mnemonic, operands, sec, addr)
                lc[sec] += size

            self.listing.append((raw.rstrip(), addr, size,
                                  f'{label+": " if label else ""}{note}'))

    def _data_directive(self, mnemonic, operands, sec, addr, lc):
        m = mnemonic.upper()
        if m == 'DB':
            size = self._calc_db_size(operands)
        elif m == 'DW':
            size = len(operands.split(',')) * 2
        elif m == 'DD':
            size = len(operands.split(',')) * 4
        elif m == 'DQ':
            size = len(operands.split(',')) * 8
        elif m == 'RESB':
            size = int(operands.strip())
        elif m == 'RESD':
            size = int(operands.strip()) * 4
        else:
            size = 0
        if m != 'EQU':
            lc[sec] += size
        return size

    def _check_reloc(self, mnemonic, operands, sec, addr) -> str:
        """偵測需要重定位的符號引用，記錄到 reltab"""
        m = mnemonic.upper()
        note = '機器碼'
        # 檢查運算元中是否含有外部符號
        for sym_name, sym in self.symtab.items():
            if sym.section == 'UNDEF' and sym_name in operands:
                rtype = 'R_X86_64_PLT32' if m == 'CALL' else 'R_X86_64_PC32'
                self.reltab.append(Relocation(
                    section=sec, offset=addr + 1,
                    symbol=sym_name, rtype=rtype, addend=-4
                ))
                note = f'→ 重定位：{sym_name} ({rtype})'
                break
        return note

    # ── 報告 ─────────────────────────────────────────────────

    def print_symtab(self):
        print(f"\n  符號表（SYMTAB）：")
        print(f"  {'名稱':<16} {'值/位址':>10} {'區段':<8} {'可見性':<8} {'類型'}")
        print(f"  {'─'*58}")
        for name, sym in sorted(self.symtab.items()):
            val = f"0x{sym.value:04X}" if sym.section not in ('ABS','UNDEF') \
                  else str(sym.value)
            print(f"  {name:<16} {val:>10} {sym.section:<8} "
                  f"{sym.bind.value:<8} {sym.stype.value}")

    def print_reltab(self):
        if not self.reltab:
            print(f"\n  重定位表：（無外部符號引用）")
            return
        print(f"\n  重定位表（.rela.text）：")
        print(f"  {'區段':<8} {'偏移':>8} {'符號':<16} {'類型':<22} {'Addend':>8}")
        print(f"  {'─'*66}")
        for r in self.reltab:
            print(f"  {r.section:<8} 0x{r.offset:04X}   {r.symbol:<16} "
                  f"{r.rtype:<22} {r.addend:>8}")

    def print_listing(self):
        print(f"\n  組譯列表（Listing）：")
        print(f"  {'行號':>4}  {'位址':>8}  {'大小':>4}  {'原始碼':<35}  注記")
        print(f"  {'─'*75}")
        for i, (raw, addr, size, note) in enumerate(self.listing, 1):
            addr_s = f"0x{addr:04X}" if size > 0 else '      '
            size_s = f"{size}B" if size > 0 else '   '
            print(f"  {i:>4}  {addr_s}  {size_s:>4}  {raw[:35]:<35}  {note}")


# ── 主程式 ────────────────────────────────────────────────────

def demo_assemble():
    print("=" * 75)
    print("  完整兩遍組譯模擬（Linux x86-64 Hello World）")
    print("=" * 75)

    source = """\
; Hello World - Linux x86-64
global _start
extern write_func

section .data
    msg      DB  "Hello, World!", 0x0a
    msg_len  EQU $ - msg

section .bss
    buffer   RESB 64

section .text
_start:
    ; sys_write(1, msg, msg_len)
    MOV  RAX, 1
    MOV  RDI, 1
    LEA  RSI, [msg]
    MOV  RDX, 13
    SYSCALL
    ; 呼叫外部函式（需重定位）
    CALL write_func
    ; sys_exit(0)
    XOR  RDI, RDI
    MOV  RAX, 60
    SYSCALL
"""

    asm = Assembler()

    print("\n  ── Pass 1：建立符號表 ───────────────────────────")
    asm.pass1(source)
    asm.print_symtab()

    print("\n  ── Pass 2：翻譯指令，產生重定位表 ──────────────")
    asm.pass2(source)
    asm.print_listing()
    asm.print_reltab()

    print(f"\n  ── 模擬 ELF .o 檔的 Section 大小 ───────────────")
    print(f"  .text  大小：{asm.lc['.text']:>6} bytes")
    print(f"  .data  大小：{asm.lc['.data']:>6} bytes")
    print(f"  .bss   大小：{asm.lc['.bss']:>6} bytes（磁碟上不佔空間）")
    print(f"  .symtab 項目：{len(asm.symtab):>4} 個符號")
    print(f"  .rela.text 項目：{len(asm.reltab):>2} 個重定位項目")


def demo_forward_reference():
    print("\n" + "=" * 75)
    print("  前向參考（Forward Reference）的解析過程")
    print("=" * 75)

    print("""
  前向參考：指令引用了後面才定義的標號

  程式碼：
    0x0000:  JMP  end_func       ; end_func 在 0x000F（Pass 1 後才知道）
    0x0005:  MOV  EAX, 1
    0x000A:  ADD  EAX, EBX
  end_func:
    0x000F:  RET

  Pass 1 掃描完後：
    SYMTAB[end_func] = 0x000F

  Pass 2 處理 JMP end_func（位於 0x0000）：
    JMP NEAR：E9 + disp32
    disp32 = 目標位址 - （當前位址 + 指令長度）
           = 0x000F - (0x0000 + 5)
           = 0x000A
    機器碼：E9 0A 00 00 00
""")

    # 實際計算
    entries = [
        (0x0000, 5,  "JMP end_func"),
        (0x0005, 5,  "MOV EAX, 1"),
        (0x000A, 3,  "ADD EAX, EBX"),
        (0x000D, 1,  "（end_func:）"),
        (0x000D, 1,  "RET"),
    ]

    print("  Pass 1 位址計算：")
    print(f"  {'位址':>8}  {'大小':>4}  原始碼")
    print(f"  {'─'*42}")
    for addr, size, label in entries:
        print(f"  0x{addr:04X}   {size:>3}B  {label}")

    jmp_addr  = 0x0000
    jmp_len   = 5
    target    = 0x000D   # end_func
    disp32    = target - (jmp_addr + jmp_len)
    print(f"\n  Pass 2 計算 JMP end_func 的 disp32：")
    print(f"    disp32 = 0x{target:04X} - (0x{jmp_addr:04X} + {jmp_len})")
    print(f"           = 0x{disp32:04X} = {disp32}")
    print(f"    機器碼：E9 {disp32 & 0xFF:02X} {(disp32>>8)&0xFF:02X} "
          f"{(disp32>>16)&0xFF:02X} {(disp32>>24)&0xFF:02X}")


if __name__ == "__main__":
    demo_assemble()
    demo_forward_reference()