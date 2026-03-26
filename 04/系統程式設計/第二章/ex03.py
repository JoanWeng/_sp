# ============================================================
#  第 2 章　習題 03 — 資料定義與數值表示
#  實作：模擬 DB/DW/DD/DQ 的記憶體佈局（小端序），
#        並展示各種數值格式的轉換
# ============================================================

import struct


# ── 記憶體模擬 ────────────────────────────────────────────────

class Memory:
    """簡易記憶體模型，以 bytearray 模擬"""

    def __init__(self, size=256):
        self.mem = bytearray(size)
        self.cursor = 0       # 模擬 Location Counter
        self.labels = {}      # 符號表

    def db(self, label, *values):
        """DB：每個值寫入 1 byte（或字串轉 bytes）"""
        addr = self.cursor
        if label:
            self.labels[label] = addr
        for v in values:
            if isinstance(v, str):
                for ch in v.encode('ascii'):
                    self.mem[self.cursor] = ch
                    self.cursor += 1
            else:
                self.mem[self.cursor] = v & 0xFF
                self.cursor += 1
        return addr

    def dw(self, label, *values):
        """DW：每個值寫入 2 bytes（小端序）"""
        addr = self.cursor
        if label:
            self.labels[label] = addr
        for v in values:
            self.mem[self.cursor:self.cursor+2] = struct.pack('<H', v & 0xFFFF)
            self.cursor += 2
        return addr

    def dd(self, label, *values):
        """DD：每個值寫入 4 bytes（小端序）"""
        addr = self.cursor
        if label:
            self.labels[label] = addr
        for v in values:
            self.mem[self.cursor:self.cursor+4] = struct.pack('<I', v & 0xFFFFFFFF)
            self.cursor += 4
        return addr

    def dq(self, label, *values):
        """DQ：每個值寫入 8 bytes（小端序）"""
        addr = self.cursor
        if label:
            self.labels[label] = addr
        for v in values:
            self.mem[self.cursor:self.cursor+8] = struct.pack('<Q', v & 0xFFFFFFFFFFFFFFFF)
            self.cursor += 8
        return addr

    def resb(self, label, n):
        """RESB：保留 n bytes（清為 0）"""
        addr = self.cursor
        if label:
            self.labels[label] = addr
        self.cursor += n
        return addr

    def dump(self, start=0, end=None, cols=16):
        """十六進位記憶體傾印"""
        end = end or self.cursor
        print(f"\n{'位址':>6}  {'十六進位內容':<{cols*3}}  ASCII")
        print("-" * (10 + cols * 3 + cols))
        for base in range(start, end, cols):
            row_bytes = self.mem[base:base+cols]
            hex_part  = ' '.join(f'{b:02X}' for b in row_bytes)
            asc_part  = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row_bytes)
            print(f"0x{base:04X}  {hex_part:<{cols*3}}  {asc_part}")


# ── 數值格式轉換示範 ─────────────────────────────────────────

def show_number_formats():
    print("=" * 60)
    print("  數值表示方式（組合語言支援的格式）")
    print("=" * 60)

    examples = [
        ("十進位",      255,        "255"),
        ("十六進位",    0xFF,       "0xFF  或  0FFh"),
        ("二進位",      0b11111111, "0b11111111  或  11111111b"),
        ("八進位",      0o377,      "0o377  或  377o"),
        ("字元 'A'",    ord('A'),   "'A'  (ASCII 65)"),
        ("字元 '\\n'",  ord('\n'),  "0x0a"),
    ]

    print(f"\n{'說明':<14} {'十進位':>8} {'十六進位':>10} {'二進位':>12} {'組語寫法'}")
    print("-" * 65)
    for desc, val, asm in examples:
        print(f"{desc:<14} {val:>8} {hex(val):>10} {bin(val):>12}   {asm}")


# ── 小端序（Little-Endian）說明 ──────────────────────────────

def show_endianness():
    print("\n" + "=" * 60)
    print("  小端序（Little-Endian）記憶體佈局")
    print("=" * 60)

    value = 0x12345678
    print(f"\n  值：0x{value:08X}  （十進位 {value}）")
    print(f"\n  以 DD（4 bytes）儲存在位址 0x0000：")
    print(f"  {'位址':<10} {'byte 值':<10} {'說明'}")
    print("  " + "-" * 40)

    packed = struct.pack('<I', value)
    for i, b in enumerate(packed):
        which = ['最低位 (LSB)', '次低位', '次高位', '最高位 (MSB)'][i]
        print(f"  0x{i:04X}      0x{b:02X}        {which}")

    print(f"\n  x86 使用小端序：低位 byte 存在低位址。")
    print(f"  記憶體中看起來像：{' '.join(f'{b:02X}' for b in packed)}（低→高）")
    print(f"  還原時反向讀取：{' '.join(f'{b:02X}' for b in reversed(packed))} → 0x{value:08X}")


# ── 主程式 ────────────────────────────────────────────────────

def main():
    # 1. 數值格式
    show_number_formats()

    # 2. 小端序
    show_endianness()

    # 3. 記憶體模擬：模擬以下 NASM .data 區段
    #
    #   section .data
    #       greeting  DB  "Hi!", 0x0a
    #       answer    DW  42
    #       big_num   DD  0xDEADBEEF
    #       arr       DD  10, 20, 30
    #       counter   DQ  0
    #       padding   RESB 4

    print("\n" + "=" * 60)
    print("  記憶體佈局模擬（.data 區段）")
    print("=" * 60)

    m = Memory(128)

    m.db('greeting', "Hi!", 0x0a)       # DB "Hi!", 0x0a
    m.dw('answer',   42)                # DW 42
    m.dd('big_num',  0xDEADBEEF)        # DD 0xDEADBEEF
    m.dd('arr',      10, 20, 30)        # DD 10, 20, 30
    m.dq('counter',  0)                 # DQ 0
    m.resb('padding', 4)                # RESB 4

    # 印出符號表
    print("\n符號表：")
    for label, addr in m.labels.items():
        print(f"  {label:<12} → 0x{addr:04X}")

    # 記憶體傾印
    print("\n記憶體傾印（前 64 bytes）：")
    m.dump(0, min(m.cursor, 64))

    # 驗證讀取
    print("\n讀取驗證：")
    ans_addr = m.labels['answer']
    ans_val  = struct.unpack('<H', m.mem[ans_addr:ans_addr+2])[0]
    print(f"  answer（0x{ans_addr:04X}）= {ans_val}  ← 應為 42  {'✓' if ans_val == 42 else '✗'}")

    big_addr = m.labels['big_num']
    big_val  = struct.unpack('<I', m.mem[big_addr:big_addr+4])[0]
    print(f"  big_num（0x{big_addr:04X}）= 0x{big_val:08X}  ← 應為 0xDEADBEEF  {'✓' if big_val == 0xDEADBEEF else '✗'}")

    arr_addr = m.labels['arr']
    arr_vals = struct.unpack('<3I', m.mem[arr_addr:arr_addr+12])
    print(f"  arr（0x{arr_addr:04X}）= {list(arr_vals)}  ← 應為 [10, 20, 30]  {'✓' if list(arr_vals) == [10, 20, 30] else '✗'}")

    total = m.cursor
    print(f"\n.data 區段總大小：{total} bytes")


if __name__ == '__main__':
    main()