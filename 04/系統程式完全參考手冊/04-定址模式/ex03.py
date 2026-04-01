# ============================================================
#  第 4 章　習題 02 — ModRM / SIB 位元組編碼與解碼
#  實作：模擬 x86 指令的 ModRM 和 SIB 位元組的
#        編碼（組語 → 機器碼）與解碼（機器碼 → 組語）
# ============================================================

# ── 暫存器編號對照表（3-bit 編碼）────────────────────────────

REG_ENCODE = {
    'RAX': 0, 'RCX': 1, 'RDX': 2, 'RBX': 3,
    'RSP': 4, 'RBP': 5, 'RSI': 6, 'RDI': 7,
    'EAX': 0, 'ECX': 1, 'EDX': 2, 'EBX': 3,
    'ESP': 4, 'EBP': 5, 'ESI': 6, 'EDI': 7,
    'R8':  8, 'R9':  9, 'R10':10, 'R11':11,
    'R12':12, 'R13':13, 'R14':14, 'R15':15,
}

REG_DECODE_32 = {v: k for k, v in REG_ENCODE.items() if k.startswith('E')}
REG_DECODE_64 = {v: k for k, v in REG_ENCODE.items() if k.startswith('R') and len(k) == 3}

SCALE_ENCODE = {1: 0b00, 2: 0b01, 4: 0b10, 8: 0b11}
SCALE_DECODE = {0b00: 1, 0b01: 2, 0b10: 4, 0b11: 8}


# ── ModRM 位元組 ─────────────────────────────────────────────

def encode_modrm(mod: int, reg: int, rm: int) -> int:
    """
    編碼 ModRM 位元組
      mod: 2-bit（0～3）
      reg: 3-bit（0～7）
      rm:  3-bit（0～7）
    """
    return ((mod & 0b11) << 6) | ((reg & 0b111) << 3) | (rm & 0b111)


def decode_modrm(byte: int) -> dict:
    """解碼 ModRM 位元組"""
    mod = (byte >> 6) & 0b11
    reg = (byte >> 3) & 0b111
    rm  = byte & 0b111
    return {'mod': mod, 'reg': reg, 'rm': rm, 'raw': byte}


# ── SIB 位元組 ───────────────────────────────────────────────

def encode_sib(scale: int, index: int, base: int) -> int:
    """
    編碼 SIB 位元組
      scale: 2-bit（0=×1, 1=×2, 2=×4, 3=×8）
      index: 3-bit（暫存器編號）
      base:  3-bit（暫存器編號）
    """
    return ((scale & 0b11) << 6) | ((index & 0b111) << 3) | (base & 0b111)


def decode_sib(byte: int) -> dict:
    """解碼 SIB 位元組"""
    scale = (byte >> 6) & 0b11
    index = (byte >> 3) & 0b111
    base  = byte & 0b111
    return {
        'scale_bits': scale,
        'scale':      SCALE_DECODE[scale],
        'index':      index,
        'base':       base,
        'raw':        byte,
    }


# ── 完整指令編碼 ──────────────────────────────────────────────

def encode_mov_r32_rm32(dst_reg: str, src_mode: dict) -> list:
    """
    編碼 MOV r32, r/m32（Opcode = 0x8B）

    src_mode 可以是：
      {'type': 'reg',     'reg': 'EBX'}
      {'type': 'direct',  'addr': 0x1234}
      {'type': 'reg_ind', 'base': 'EBX'}
      {'type': 'base_d8', 'base': 'EBX', 'disp': 8}
      {'type': 'base_d32','base': 'EBX', 'disp': 500}
      {'type': 'sib',     'base': 'EBX', 'index': 'ECX', 'scale': 4, 'disp': 0}
    """
    opcode = 0x8B
    dst    = REG_ENCODE[dst_reg] & 0b111  # 只取低 3 位（簡化，不處理 REX）
    result = [opcode]
    t      = src_mode['type']

    if t == 'reg':
        src = REG_ENCODE[src_mode['reg']] & 0b111
        result.append(encode_modrm(0b11, dst, src))

    elif t == 'reg_ind':
        base = REG_ENCODE[src_mode['base']] & 0b111
        if base == 4:  # RSP/ESP 需要 SIB
            result.append(encode_modrm(0b00, dst, 0b100))
            result.append(encode_sib(0b00, 0b100, 0b100))  # no index, base=RSP
        elif base == 5:  # RBP/EBP 需要用 disp8=0
            result.append(encode_modrm(0b01, dst, base))
            result.append(0x00)
        else:
            result.append(encode_modrm(0b00, dst, base))

    elif t == 'base_d8':
        base = REG_ENCODE[src_mode['base']] & 0b111
        disp = src_mode['disp'] & 0xFF
        result.append(encode_modrm(0b01, dst, base))
        result.append(disp)

    elif t == 'base_d32':
        base = REG_ENCODE[src_mode['base']] & 0b111
        disp = src_mode['disp'] & 0xFFFFFFFF
        result.append(encode_modrm(0b10, dst, base))
        # disp32 小端序
        result.extend([disp & 0xFF, (disp >> 8) & 0xFF,
                        (disp >> 16) & 0xFF, (disp >> 24) & 0xFF])

    elif t == 'sib':
        base  = REG_ENCODE[src_mode['base']] & 0b111
        index = REG_ENCODE[src_mode['index']] & 0b111
        scale = SCALE_ENCODE[src_mode['scale']]
        disp  = src_mode.get('disp', 0)

        if disp == 0:
            result.append(encode_modrm(0b00, dst, 0b100))  # R/M=4 表示 SIB follows
        elif -128 <= disp <= 127:
            result.append(encode_modrm(0b01, dst, 0b100))
        else:
            result.append(encode_modrm(0b10, dst, 0b100))

        result.append(encode_sib(scale, index, base))

        if disp != 0:
            if -128 <= disp <= 127:
                result.append(disp & 0xFF)
            else:
                d = disp & 0xFFFFFFFF
                result.extend([d & 0xFF, (d >> 8) & 0xFF,
                                (d >> 16) & 0xFF, (d >> 24) & 0xFF])

    return result


def disassemble_modrm(opcode: int, bytes_: list) -> str:
    """
    簡易反組譯：給定 opcode 和後續 bytes，回傳組語字串
    只支援 0x8B（MOV r32, r/m32）
    """
    if opcode != 0x8B:
        return f"未知 opcode: 0x{opcode:02X}"

    idx  = 0
    mrm  = decode_modrm(bytes_[idx]); idx += 1
    mod  = mrm['mod']
    reg  = mrm['reg']
    rm   = mrm['rm']

    dst_name = REG_DECODE_32.get(reg, f'R{reg}')

    def get_reg_name(code):
        return REG_DECODE_32.get(code, f'R{code}')

    if mod == 0b11:
        src = f"{get_reg_name(rm)}"
    elif mod == 0b00 and rm == 0b100:   # SIB
        sib   = decode_sib(bytes_[idx]); idx += 1
        scale = sib['scale']
        bidx  = get_reg_name(sib['index'])
        bbase = get_reg_name(sib['base'])
        if scale == 1:
            src = f"[{bbase} + {bidx}]"
        else:
            src = f"[{bbase} + {bidx}*{scale}]"
    elif mod == 0b00:
        src = f"[{get_reg_name(rm)}]"
    elif mod == 0b01:
        disp  = bytes_[idx]; idx += 1
        disp  = disp if disp < 128 else disp - 256  # sign-extend
        sign  = '+' if disp >= 0 else '-'
        src   = f"[{get_reg_name(rm)} {sign} {abs(disp)}]"
    else:  # mod == 0b10
        disp  = bytes_[idx] | (bytes_[idx+1] << 8) | \
                (bytes_[idx+2] << 16) | (bytes_[idx+3] << 24)
        idx  += 4
        sign  = '+' if disp >= 0 else '-'
        src   = f"[{get_reg_name(rm)} {sign} {abs(disp)}]"

    return f"MOV {dst_name}, {src}"


# ── 主程式 ───────────────────────────────────────────────────

def demo_encoding():
    print("=" * 65)
    print("  ModRM / SIB 位元組編碼示範")
    print("=" * 65)
    print("""
  ModRM 位元組結構：
    [7:6] Mod  — 00=記憶體無位移, 01=記憶體disp8,
                 10=記憶體disp32, 11=暫存器
    [5:3] Reg  — 目的暫存器編號（或 opcode 擴展）
    [2:0] R/M  — 來源暫存器編號（或記憶體基底）

  SIB 位元組結構（當 R/M=100 時跟在 ModRM 之後）：
    [7:6] Scale — 00=×1, 01=×2, 10=×4, 11=×8
    [5:3] Index — 索引暫存器編號
    [2:0] Base  — 基底暫存器編號
""")

    test_cases = [
        ("MOV EAX, EBX",         'EAX', {'type': 'reg',     'reg': 'EBX'}),
        ("MOV EAX, [EBX]",       'EAX', {'type': 'reg_ind', 'base': 'EBX'}),
        ("MOV EAX, [EBX + 8]",   'EAX', {'type': 'base_d8', 'base': 'EBX', 'disp': 8}),
        ("MOV EAX, [EBX - 4]",   'EAX', {'type': 'base_d8', 'base': 'EBX', 'disp': -4}),
        ("MOV EAX, [EBX + 500]", 'EAX', {'type': 'base_d32','base': 'EBX', 'disp': 500}),
        ("MOV EAX, [EBX+ECX*4]", 'EAX', {'type': 'sib',
                                           'base': 'EBX', 'index': 'ECX',
                                           'scale': 4, 'disp': 0}),
        ("MOV EAX,[EBX+ECX*4+8]",'EAX', {'type': 'sib',
                                           'base': 'EBX', 'index': 'ECX',
                                           'scale': 4, 'disp': 8}),
    ]

    print(f"  {'組語指令':<28} {'機器碼（hex）':<30} {'反組譯驗證'}")
    print("  " + "-" * 80)

    for asm, dst, src_mode in test_cases:
        encoded = encode_mov_r32_rm32(dst, src_mode)
        hex_str = ' '.join(f'{b:02X}' for b in encoded)

        # 反組譯驗證
        disasm  = disassemble_modrm(encoded[0], encoded[1:])

        match = "✓" if asm.replace(' ','').upper() == disasm.replace(' ','').upper() else "~"
        print(f"  {asm:<28} {hex_str:<30} {disasm}  {match}")


def demo_modrm_breakdown():
    print("\n" + "=" * 65)
    print("  ModRM 位元組逐位元解析")
    print("=" * 65)

    examples = [
        (0x8B, 0xC3, "MOV EAX, EBX"),
        (0x8B, 0x03, "MOV EAX, [EBX]"),
        (0x8B, 0x43, "MOV EAX, [EBX + disp8]"),
        (0x8B, 0x04, "MOV EAX, [SIB]"),
    ]

    for opcode, modrm_byte, desc in examples:
        m = decode_modrm(modrm_byte)
        print(f"\n  指令：{desc}")
        print(f"  ModRM = 0x{modrm_byte:02X} = {modrm_byte:08b}b")
        print(f"    Mod [{modrm_byte:08b}[7:6]] = {m['mod']:02b}  "
              f"→ {'暫存器' if m['mod']==3 else '記憶體(disp'+str([0,8,32][min(m['mod'],2)])+')'}")
        print(f"    Reg [{modrm_byte:08b}[5:3]] = {m['reg']:03b}  "
              f"→ {REG_DECODE_32.get(m['reg'], '?')}（目的暫存器）")
        print(f"    R/M [{modrm_byte:08b}[2:0]] = {m['rm']:03b}  "
              f"→ {REG_DECODE_32.get(m['rm'], '?（或 SIB）')}（來源）")


def demo_scale_selection():
    print("\n" + "=" * 65)
    print("  Scale 選擇對照（陣列元素大小 → Scale 值）")
    print("=" * 65)

    types = [
        ('char / uint8_t',  1, 'DB', 'BYTE',  'RESB'),
        ('short / uint16_t',2, 'DW', 'WORD',  'RESW'),
        ('int / uint32_t',  4, 'DD', 'DWORD', 'RESD'),
        ('long / uint64_t', 8, 'DQ', 'QWORD', 'RESQ'),
    ]

    print(f"\n  {'C 型別':<18} {'Size':>5} {'Scale':>6} {'NASM宣告':>8} {'指標'} {'存取範例'}")
    print("  " + "-" * 72)
    for ctype, size, define, ptr, res in types:
        scale = size
        asm_access = f"[arr + RCX*{scale}]"
        print(f"  {ctype:<18} {size:>5}     ×{scale}  {define:>8}  {ptr:<6} {asm_access}")

    print("""
  ★ 當結構體大小不是 1/2/4/8 時，Scale 無法直接使用！
    例如 sizeof(struct) = 12，必須先用 IMUL 計算偏移：

      ; 存取 struct_arr[i]（sizeof = 12）
      mov  eax, ecx      ; eax = i
      imul eax, 12       ; eax = i × 12
      mov  edx, [rbx + rax]   ; 讀取 struct_arr[i].first_field
""")


if __name__ == "__main__":
    demo_encoding()
    demo_modrm_breakdown()
    demo_scale_selection()