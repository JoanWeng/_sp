# ============================================================
#  第 4 章　習題 01 — 有效位址（EA）計算器
#  實作：模擬六大定址模式的有效位址計算，
#        並展示各模式對應的使用場景
# ============================================================

class CPU:
    """簡易 CPU 狀態模擬（只含暫存器與記憶體）"""

    def __init__(self):
        # 暫存器
        self.regs = {
            'RAX': 0, 'RBX': 0x601000, 'RCX': 3,    'RDX': 0,
            'RSP': 0x7FFF0000, 'RBP': 0x7FFF0010,
            'RSI': 0x602000,   'RDI': 0x603000,
            'R8':  0,          'R9':  0,
        }
        # 簡易記憶體（位址 → 值）
        self.mem = {}

    def reg(self, name: str) -> int:
        return self.regs.get(name.upper(), 0)

    def set_reg(self, name: str, val: int):
        self.regs[name.upper()] = val & 0xFFFFFFFFFFFFFFFF

    def write32(self, addr: int, val: int):
        self.mem[addr] = val & 0xFFFFFFFF

    def read32(self, addr: int) -> int:
        return self.mem.get(addr, 0xDEADBEEF)  # 未初始化返回哨兵值


def compute_ea(cpu: CPU, mode: str, **kwargs) -> int:
    """
    計算有效位址（Effective Address）

    mode 可以是：
      'immediate'         : 立即值（無 EA，資料即值）
      'register'          : 暫存器（無 EA，直接存取）
      'direct'            : 直接定址 [addr]
      'reg_indirect'      : 暫存器間接 [base]
      'base_disp'         : 基底+位移 [base + disp]
      'sib'               : SIB [base + index*scale + disp]

    kwargs:
      imm, reg, addr, base, index, scale, disp
    """
    if mode == 'immediate':
        return None  # 立即值無 EA
    elif mode == 'register':
        return None  # 暫存器無 EA
    elif mode == 'direct':
        return kwargs['addr']
    elif mode == 'reg_indirect':
        return cpu.reg(kwargs['base'])
    elif mode == 'base_disp':
        base = cpu.reg(kwargs['base'])
        disp = kwargs.get('disp', 0)
        return (base + disp) & 0xFFFFFFFFFFFFFFFF
    elif mode == 'sib':
        base  = cpu.reg(kwargs.get('base', 'RAX')) if kwargs.get('base') else 0
        index = cpu.reg(kwargs['index']) if kwargs.get('index') else 0
        scale = kwargs.get('scale', 1)
        disp  = kwargs.get('disp', 0)
        return (base + index * scale + disp) & 0xFFFFFFFFFFFFFFFF
    return 0


def demo_all_modes():
    cpu = CPU()

    # 初始化一些記憶體值
    cpu.write32(cpu.reg('RBX'),       0x0000_00AA)
    cpu.write32(cpu.reg('RBX') + 8,   0x0000_00BB)
    cpu.write32(cpu.reg('RBX') + 12,  0x0000_00CC)
    cpu.write32(0x601010,             0x0000_00DD)

    # 設定陣列（int_arr 從 0x601000 開始）
    for i in range(5):
        cpu.write32(cpu.reg('RBX') + i * 4, (i + 1) * 10)

    print("=" * 65)
    print("  有效位址（Effective Address）計算示範")
    print("=" * 65)

    print("\n  初始暫存器狀態：")
    for name, val in cpu.regs.items():
        print(f"    {name:4s} = 0x{val:016X}")

    cases = [
        # (說明, mode, kwargs, 組語範例)
        ("立即值定址",
         'immediate', {'imm': 42},
         "MOV EAX, 42"),

        ("暫存器定址",
         'register', {'reg': 'RBX'},
         "MOV EAX, EBX"),

        ("直接定址",
         'direct', {'addr': 0x601010},
         "MOV EAX, [0x601010]"),

        ("暫存器間接",
         'reg_indirect', {'base': 'RBX'},
         "MOV EAX, [RBX]"),

        ("基底+位移（正）",
         'base_disp', {'base': 'RBX', 'disp': 8},
         "MOV EAX, [RBX + 8]"),

        ("基底+位移（負，堆疊變數）",
         'base_disp', {'base': 'RBP', 'disp': -4},
         "MOV EAX, [RBP - 4]"),

        ("SIB：陣列存取 arr[RCX]",
         'sib', {'base': 'RBX', 'index': 'RCX', 'scale': 4, 'disp': 0},
         "MOV EAX, [RBX + RCX*4]  ; arr[3]"),

        ("SIB：結構體陣列 arr[RCX].field",
         'sib', {'base': 'RBX', 'index': 'RCX', 'scale': 4, 'disp': 8},
         "MOV EAX, [RBX + RCX*4 + 8]"),
    ]

    print(f"\n  {'定址模式':<22} {'有效位址':>18} {'記憶體值':>12}  組語範例")
    print("  " + "-" * 80)

    for desc, mode, kwargs, asm in cases:
        ea = compute_ea(cpu, mode, **kwargs)
        if ea is None:
            ea_str = "（無 EA）"
            val_str = str(kwargs.get('imm', kwargs.get('reg', '—')))
        else:
            ea_str  = f"0x{ea:016X}"
            mem_val = cpu.read32(ea)
            if mem_val == 0xDEADBEEF:
                val_str = "未初始化"
            else:
                val_str = f"0x{mem_val:08X}"
        print(f"  {desc:<22} {ea_str:>18} {val_str:>12}  {asm}")


def demo_array_access():
    print("\n" + "=" * 65)
    print("  陣列存取的 SIB 定址模式詳解")
    print("=" * 65)

    cpu = CPU()
    BASE = 0x601000
    cpu.set_reg('RBX', BASE)

    # 定義四種型別的陣列
    arrays = {
        'byte_arr  (DB, scale=1)': (1, [10, 20, 30, 40, 50]),
        'word_arr  (DW, scale=2)': (2, [100, 200, 300, 400]),
        'int_arr   (DD, scale=4)': (4, [1000, 2000, 3000]),
        'long_arr  (DQ, scale=8)': (8, [10000, 20000]),
    }

    addr = BASE
    arr_starts = {}
    for name, (elem_size, values) in arrays.items():
        arr_starts[name] = addr
        for v in values:
            cpu.write32(addr, v)
            addr += elem_size

    print("\n  以 RBX 為基底，RCX 為索引，存取各型別陣列：")
    print(f"\n  {'陣列':<30} {'索引':>4} {'有效位址':>18} {'值':>8}  組語")
    print("  " + "-" * 80)

    for name, (scale, values) in arrays.items():
        cpu.set_reg('RBX', arr_starts[name])
        for i in range(len(values)):
            cpu.set_reg('RCX', i)
            ea = compute_ea(cpu, 'sib',
                            base='RBX', index='RCX', scale=scale, disp=0)
            val = cpu.read32(ea)
            asm = f"[RBX + RCX*{scale}]"
            print(f"  {name:<30} {i:>4} 0x{ea:016X} {val:>8}  {asm}")
        print()


def demo_struct_field():
    print("=" * 65)
    print("  結構體欄位存取（Base + Displacement）")
    print("=" * 65)

    print("""
  C 語言結構體：
    struct Point3D {
        int x;      // 偏移 0，4 bytes
        int y;      // 偏移 4，4 bytes
        int z;      // 偏移 8，4 bytes
    };              // sizeof = 12 bytes
""")

    cpu = CPU()
    BASE = 0x601000
    cpu.set_reg('RBX', BASE)

    # 寫入結構體資料
    cpu.write32(BASE + 0,  10)   # x = 10
    cpu.write32(BASE + 4,  20)   # y = 20
    cpu.write32(BASE + 8,  30)   # z = 30

    POINT_X, POINT_Y, POINT_Z = 0, 4, 8

    fields = [
        ('p.x', POINT_X, "MOV EAX, [RBX + 0]"),
        ('p.y', POINT_Y, "MOV EAX, [RBX + 4]"),
        ('p.z', POINT_Z, "MOV EAX, [RBX + 8]"),
    ]

    print(f"  假設 RBX = 0x{BASE:016X}（Point3D 的起始位址）\n")
    print(f"  {'欄位':<6} {'偏移':>6} {'有效位址':>18} {'值':>6}  組語")
    print("  " + "-" * 60)

    for fname, offset, asm in fields:
        ea  = compute_ea(cpu, 'base_disp', base='RBX', disp=offset)
        val = cpu.read32(ea)
        print(f"  {fname:<6} {offset:>6} 0x{ea:016X} {val:>6}  {asm}")


def demo_lea():
    print("\n" + "=" * 65)
    print("  LEA 指令：計算位址但不存取記憶體")
    print("=" * 65)

    cpu = CPU()
    cpu.set_reg('RBX', 100)
    cpu.set_reg('RCX', 5)

    print(f"\n  初始：RBX = {cpu.reg('RBX')},  RCX = {cpu.reg('RCX')}\n")

    lea_cases = [
        ("取得變數位址",      "LEA RAX, [var]",            0x601000,          "等同 &var"),
        ("×3 快速乘法",       "LEA EAX, [RBX + RBX*2]",
         cpu.reg('RBX') + cpu.reg('RBX') * 2,             "RBX × 3"),
        ("×5 快速乘法",       "LEA EAX, [RBX + RBX*4]",
         cpu.reg('RBX') + cpu.reg('RBX') * 4,             "RBX × 5"),
        ("×9 快速乘法",       "LEA EAX, [RBX + RBX*8]",
         cpu.reg('RBX') + cpu.reg('RBX') * 8,             "RBX × 9"),
        ("三運算元加法",      "LEA EAX, [RBX + RCX + 20]",
         cpu.reg('RBX') + cpu.reg('RCX') + 20,            "RBX + RCX + 20"),
    ]

    print(f"  {'說明':<16} {'指令':<30} {'EAX 結果':>12}  {'備註'}")
    print("  " + "-" * 70)
    for desc, asm, result, note in lea_cases:
        print(f"  {desc:<16} {asm:<30} {result:>12}  {note}")

    print("""
  ★ 重點：LEA 不存取記憶體，只計算方括號內的算術式
          因此 LEA EAX, [RBX + RBX*4] 不需要 RBX 是有效的記憶體位址
          純粹當作「加法 + 乘法」的捷徑使用
""")


if __name__ == "__main__":
    demo_all_modes()
    demo_array_access()
    demo_struct_field()
    demo_lea()