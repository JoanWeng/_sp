# ============================================================
#  第 9 章　習題 01 — 連結器模擬：符號解析與重定位
#  實作：模擬連結器的 E/U/D 集合演算法、強弱符號規則、
#        重定位計算，以及靜態程式庫的按需取用機制
# ============================================================

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SymBind(Enum):
    LOCAL  = "LOCAL"
    GLOBAL = "GLOBAL"
    WEAK   = "WEAK"
    EXTERN = "EXTERN"

class SymSec(Enum):
    TEXT   = ".text"
    DATA   = ".data"
    BSS    = ".bss"
    ABS    = "ABS"
    UNDEF  = "UNDEF"
    COMMON = "COMMON"

@dataclass
class Symbol:
    name:    str
    value:   int
    section: SymSec
    bind:    SymBind = SymBind.GLOBAL
    size:    int = 0
    origin:  str = ""   # 來自哪個目的檔

@dataclass
class RelocEntry:
    section:     str
    offset:      int
    symbol:      str
    rtype:       str
    addend:      int = -4

@dataclass
class ObjectFile:
    name:     str
    symbols:  list[Symbol]  = field(default_factory=list)
    relocs:   list[RelocEntry] = field(default_factory=list)
    text_size: int = 0
    data_size: int = 0
    bss_size:  int = 0


# ── 連結器主體 ────────────────────────────────────────────────

class Linker:

    def __init__(self, text_base: int = 0x0040_0000,
                 data_base: int = 0x0060_0000):
        self.text_base = text_base
        self.data_base = data_base

        # 三個集合（符號解析演算法）
        self.E: list[str]        = []   # Examined（已處理的目的檔名稱）
        self.U: set[str]         = set()# Undefined（未解析的符號名稱）
        self.D: dict[str, Symbol]= {}   # Defined（已解析的符號：名稱→Symbol）

        # 最終符號表與重定位表
        self.global_symtab: dict[str, Symbol] = {}
        self.all_relocs:    list[RelocEntry]  = []

        # 合併後的區段大小
        self.text_cursor = text_base
        self.data_cursor = data_base
        self.bss_cursor  = 0

        self.log: list[str] = []

    # ── 符號解析 ──────────────────────────────────────────────

    def _resolve_symbol(self, new_sym: Symbol, from_file: str):
        """處理單一符號，維護 D/U 集合，套用強弱符號規則"""
        name = new_sym.name

        if new_sym.section == SymSec.UNDEF:
            # 外部引用：若 D 中沒有 → 加入 U
            if name not in self.D:
                self.U.add(name)
                self.log.append(
                    f"    [{from_file}] UNDEF {name} → 加入 U 集合")
        else:
            # 有定義：加入或更新 D，從 U 移除
            if name in self.D:
                existing = self.D[name]
                # 強強衝突
                if (existing.bind == SymBind.GLOBAL and
                        new_sym.bind == SymBind.GLOBAL):
                    self.log.append(
                        f"    ❌ 錯誤：強符號 '{name}' 在 {existing.origin} "
                        f"和 {from_file} 中重複定義！")
                    return
                # 弱符號被強符號覆蓋
                elif existing.bind == SymBind.WEAK and new_sym.bind == SymBind.GLOBAL:
                    self.log.append(
                        f"    [{from_file}] 強符號 {name} 覆蓋 {existing.origin} 的弱符號")
                    new_sym.origin = from_file
                    self.D[name] = new_sym
                elif existing.bind == SymBind.GLOBAL and new_sym.bind == SymBind.WEAK:
                    self.log.append(
                        f"    [{from_file}] 弱符號 {name} 被 {existing.origin} 的強符號忽略")
                else:
                    self.log.append(
                        f"    [{from_file}] 弱-弱衝突 {name}，保留 {existing.origin}")
            else:
                new_sym.origin = from_file
                self.D[name] = new_sym
                self.log.append(
                    f"    [{from_file}] 定義 {name} ({new_sym.section.value}) → 加入 D")
            self.U.discard(name)

    def add_object(self, obj: ObjectFile):
        """將一個目的檔加入連結"""
        self.log.append(f"\n  處理 {obj.name}：")
        self.E.append(obj.name)

        # 分配載入位址
        obj._text_base = self.text_cursor
        obj._data_base = self.data_cursor
        self.text_cursor += obj.text_size
        self.data_cursor += obj.data_size
        self.bss_cursor  += obj.bss_size

        # 重定位到位址後更新符號值
        for sym in obj.symbols:
            updated = Symbol(
                name=sym.name, section=sym.section,
                bind=sym.bind, size=sym.size,
                value=(sym.value + obj._text_base if sym.section == SymSec.TEXT
                       else sym.value + obj._data_base if sym.section == SymSec.DATA
                       else sym.value),
                origin=obj.name,
            )
            self.global_symtab[sym.name] = updated
            if sym.bind != SymBind.LOCAL:
                self._resolve_symbol(updated, obj.name)

        # 收集重定位表
        for r in obj.relocs:
            adjusted = RelocEntry(
                section=r.section,
                offset=r.offset + obj._text_base,
                symbol=r.symbol,
                rtype=r.rtype,
                addend=r.addend,
            )
            self.all_relocs.append(adjusted)

    def add_archive(self, archive_name: str, members: list[ObjectFile]):
        """處理靜態程式庫（只取用能解析 U 的成員）"""
        self.log.append(f"\n  處理靜態程式庫 {archive_name}：")
        changed = True
        while changed:
            changed = False
            for member in members:
                if member.name in self.E:
                    continue
                # 確認此成員是否能解析 U 中的符號
                defined_names = {s.name for s in member.symbols
                                 if s.section != SymSec.UNDEF}
                if defined_names & self.U:
                    self.log.append(
                        f"    從 {archive_name} 取用 {member.name} "
                        f"（解析 {defined_names & self.U}）")
                    self.add_object(member)
                    changed = True
                else:
                    self.log.append(
                        f"    跳過 {member.name}（不解析任何未定義符號）")

    def link(self) -> bool:
        """完成連結，回報是否成功"""
        if self.U:
            for sym in self.U:
                self.log.append(f"  ❌ undefined reference to '{sym}'")
            return False
        return True

    # ── 重定位計算 ────────────────────────────────────────────

    def apply_relocations(self):
        """執行所有重定位，計算最終填入值"""
        results = []
        for r in self.all_relocs:
            if r.symbol not in self.global_symtab:
                results.append((r, None, f"❌ 符號 {r.symbol} 未定義"))
                continue
            S = self.global_symtab[r.symbol].value
            P = r.offset
            A = r.addend

            if r.rtype in ('R_X86_64_64',):
                value = S + A
                desc  = f"S+A = 0x{S:X}+({A}) = 0x{value:X}"
            elif r.rtype in ('R_X86_64_PC32', 'R_X86_64_PLT32'):
                value = S + A - P
                desc  = f"S+A-P = 0x{S:X}+({A})-0x{P:X} = 0x{value & 0xFFFFFFFF:X}"
            elif r.rtype == 'R_X86_64_32S':
                value = S + A
                desc  = f"S+A = 0x{S:X}+({A}) = 0x{value:X}"
            else:
                value = S + A
                desc  = f"0x{value:X}"

            results.append((r, value, desc))
        return results

    # ── 報告 ─────────────────────────────────────────────────

    def print_log(self):
        print("\n  連結器執行記錄：")
        for line in self.log:
            print(line)

    def print_sets(self):
        print(f"\n  E（已處理）：{self.E}")
        print(f"  D（已定義）：{sorted(self.D.keys())}")
        print(f"  U（未定義）：{sorted(self.U)}")

    def print_symtab(self):
        print(f"\n  最終符號表：")
        print(f"  {'名稱':<20} {'位址':>12} {'區段':<8} {'可見性':<8} {'來源'}")
        print(f"  {'─'*62}")
        for name, sym in sorted(self.global_symtab.items()):
            val = f"0x{sym.value:08X}" if sym.section != SymSec.UNDEF else "UNDEF"
            print(f"  {name:<20} {val:>12} {sym.section.value:<8} "
                  f"{sym.bind.value:<8} {sym.origin}")

    def print_relocs(self, results):
        print(f"\n  重定位結果：")
        print(f"  {'偏移':>12} {'符號':<16} {'類型':<22} {'計算值'}")
        print(f"  {'─'*68}")
        for r, val, desc in results:
            val_s = f"0x{val & 0xFFFFFFFF:08X}" if val is not None else "N/A"
            print(f"  0x{r.offset:08X}   {r.symbol:<16} {r.rtype:<22} {val_s}  ({desc})")


# ── 示範 ──────────────────────────────────────────────────────

def demo_symbol_resolution():
    print("=" * 70)
    print("  示範 1：符號解析（E/U/D 集合演算法）")
    print("=" * 70)

    # 模擬三個目的檔
    main_o = ObjectFile(
        name="main.o", text_size=0x50, data_size=0,
        symbols=[
            Symbol("main",    0x00, SymSec.TEXT,  SymBind.GLOBAL),
            Symbol("printf",  0x00, SymSec.UNDEF, SymBind.EXTERN),
            Symbol("add",     0x00, SymSec.UNDEF, SymBind.EXTERN),
        ],
        relocs=[
            RelocEntry(".text", 0x10, "printf", "R_X86_64_PLT32"),
            RelocEntry(".text", 0x25, "add",    "R_X86_64_PLT32"),
        ]
    )

    math_o = ObjectFile(
        name="math.o", text_size=0x30,
        symbols=[
            Symbol("add",      0x00, SymSec.TEXT,  SymBind.GLOBAL),
            Symbol("multiply", 0x20, SymSec.TEXT,  SymBind.GLOBAL),
        ],
    )

    # 靜態程式庫 libutil.a 的成員
    util1_o = ObjectFile(
        name="util1.o", text_size=0x20,
        symbols=[
            Symbol("helper_a", 0x00, SymSec.TEXT, SymBind.GLOBAL),
        ],
    )
    util2_o = ObjectFile(
        name="util2.o", text_size=0x10,
        symbols=[
            Symbol("printf", 0x00, SymSec.TEXT, SymBind.GLOBAL),
        ],
    )

    linker = Linker()

    print("\n  連結順序：main.o  math.o  libutil.a")
    linker.add_object(main_o)
    linker.add_object(math_o)
    linker.add_archive("libutil.a", [util1_o, util2_o])

    success = linker.link()
    linker.print_log()
    linker.print_sets()
    linker.print_symtab()

    results = linker.apply_relocations()
    linker.print_relocs(results)

    print(f"\n  連結結果：{'✅ 成功' if success else '❌ 失敗'}")


def demo_strong_weak():
    print("\n" + "=" * 70)
    print("  示範 2：強符號 vs 弱符號")
    print("=" * 70)

    print("""
  強符號（Strong）：一般全域函式與已初始化的全域變數
  弱符號（Weak）  ：__attribute__((weak)) 修飾的符號

  規則：
    強 + 強 → 連結錯誤（重複定義）
    強 + 弱 → 選強符號（弱符號被忽略）
    弱 + 弱 → 任選其一（行為未定義）
""")

    scenarios = [
        ("強 + 強衝突", [
            ObjectFile("a.o", text_size=0x10,
                       symbols=[Symbol("foo", 0, SymSec.TEXT, SymBind.GLOBAL)]),
            ObjectFile("b.o", text_size=0x10,
                       symbols=[Symbol("foo", 0, SymSec.TEXT, SymBind.GLOBAL)]),
        ]),
        ("強 + 弱：選強符號", [
            ObjectFile("a.o", text_size=0x10,
                       symbols=[Symbol("bar", 0, SymSec.TEXT, SymBind.GLOBAL)]),
            ObjectFile("b.o", text_size=0x20,
                       symbols=[Symbol("bar", 0, SymSec.TEXT, SymBind.WEAK)]),
        ]),
        ("弱 + 強：先弱後強", [
            ObjectFile("a.o", text_size=0x10,
                       symbols=[Symbol("baz", 0, SymSec.TEXT, SymBind.WEAK)]),
            ObjectFile("b.o", text_size=0x20,
                       symbols=[Symbol("baz", 0, SymSec.TEXT, SymBind.GLOBAL)]),
        ]),
    ]

    for desc, objs in scenarios:
        print(f"  ── {desc} ──")
        linker = Linker()
        for obj in objs:
            linker.add_object(obj)
        linker.link()
        for line in linker.log:
            if line.strip():
                print(f"  {line.strip()}")
        if 'baz' in linker.D or 'bar' in linker.D:
            sym_name = 'baz' if 'baz' in linker.D else 'bar'
            chosen = linker.D[sym_name]
            print(f"  → 最終選用：{sym_name} 來自 {chosen.origin}")
        print()


def demo_relocation_calculation():
    print("=" * 70)
    print("  示範 3：重定位計算（R_X86_64_PC32 / R_X86_64_PLT32）")
    print("=" * 70)

    print("""
  情境：
    main.o 中 CALL printf（位於 .text 偏移 0x10）
    printf 最終位址 = 0x0040_8020（libc 中）
    CALL 指令的 imm32 欄位位於 0x0040_1011
    addend = -4（PC 相對）

  公式（R_X86_64_PLT32）：
    填入值 = S + A - P
           = printf_addr + (-4) - field_addr

  計算：
""")

    TEXT_BASE   = 0x0040_1000
    PRINTF_ADDR = 0x0040_8020
    CALL_OFFSET = 0x10          # CALL 指令在 .text 內的偏移
    IMM32_FIELD = TEXT_BASE + CALL_OFFSET + 1  # imm32 在 CALL+1 的位置

    S = PRINTF_ADDR
    P = IMM32_FIELD
    A = -4
    result = (S + A - P) & 0xFFFFFFFF

    print(f"    S（printf 位址）  = 0x{S:08X}")
    print(f"    P（欄位位址）     = 0x{P:08X}")
    print(f"    A（addend）       = {A}")
    print(f"    填入值 = 0x{S:08X} + ({A}) - 0x{P:08X}")
    print(f"           = 0x{result:08X}")
    print(f"\n    CALL 指令機器碼（連結後）：")
    b = result.to_bytes(4, 'little')
    print(f"      E8 {b[0]:02X} {b[1]:02X} {b[2]:02X} {b[3]:02X}")

    print(f"""
  驗證：
    CPU 執行 CALL 時：
    下一條指令位址 = CALL 指令位址 + 5 = 0x{TEXT_BASE + CALL_OFFSET + 5:08X}
    跳躍目標       = 下一條指令位址 + 填入值（有號擴展）
                   = 0x{TEXT_BASE + CALL_OFFSET + 5:08X} + 0x{result:08X}（有號）
                   = 0x{(TEXT_BASE + CALL_OFFSET + 5 + result) & 0xFFFFFFFFFFFFFFFF:08X}
    應等於 printf  = 0x{PRINTF_ADDR:08X}  {'✓' if (TEXT_BASE + CALL_OFFSET + 5 + result) % (2**32) == PRINTF_ADDR else '✗'}
""")


def demo_archive_order():
    print("=" * 70)
    print("  示範 4：靜態程式庫的連結順序（Order Matters！）")
    print("=" * 70)

    print("""
  情境：main.o 使用 foo()，libfoo.a 提供 foo()

  規則：程式庫必須放在所有引用它的目的檔之後！
""")

    main_o = ObjectFile(
        name="main.o", text_size=0x20,
        symbols=[
            Symbol("main", 0, SymSec.TEXT,  SymBind.GLOBAL),
            Symbol("foo",  0, SymSec.UNDEF, SymBind.EXTERN),
        ],
    )
    foo_o = ObjectFile(
        name="foo.o", text_size=0x10,
        symbols=[Symbol("foo", 0, SymSec.TEXT, SymBind.GLOBAL)],
    )

    print("  ── ❌ 錯誤：libfoo.a 在 main.o 之前 ──")
    linker1 = Linker()
    linker1.add_archive("libfoo.a", [foo_o])
    linker1.add_object(main_o)
    success1 = linker1.link()
    for line in linker1.log:
        if line.strip():
            print(f"  {line.strip()}")
    print(f"  結果：{'✅ 成功' if success1 else '❌ 失敗（undefined reference to foo）'}\n")

    print("  ── ✅ 正確：main.o 在 libfoo.a 之前 ──")
    linker2 = Linker()
    linker2.add_object(main_o)
    linker2.add_archive("libfoo.a", [foo_o])
    success2 = linker2.link()
    for line in linker2.log:
        if line.strip():
            print(f"  {line.strip()}")
    print(f"  結果：{'✅ 成功' if success2 else '❌ 失敗'}")


if __name__ == "__main__":
    demo_symbol_resolution()
    demo_strong_weak()
    demo_relocation_calculation()
    demo_archive_order()