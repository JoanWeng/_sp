def compute_flags_add(a: int, b: int, bits: int = 32) -> dict:
    mask     = (1 << bits) - 1
    sign_bit = 1 << (bits - 1)

    result_full = a + b
    result      = result_full & mask

    CF = 1 if result_full > mask else 0
    ZF = 1 if result == 0 else 0
    SF = 1 if (result & sign_bit) != 0 else 0

    a_sign = 1 if (a & sign_bit) != 0 else 0
    b_sign = 1 if (b & sign_bit) != 0 else 0
    OF = 1 if (a_sign == b_sign) and (SF != a_sign) else 0

    PF = 1 if bin(result & 0xFF).count('1') % 2 == 0 else 0
    AF = 1 if ((a & 0xF) + (b & 0xF)) > 0xF else 0

    return {'result': result, 'bits': bits,
            'CF': CF, 'ZF': ZF, 'SF': SF, 'OF': OF, 'PF': PF, 'AF': AF}


def compute_flags_sub(a: int, b: int, bits: int = 32) -> dict:
    mask     = (1 << bits) - 1
    sign_bit = 1 << (bits - 1)

    result_full = a - b
    result      = result_full & mask

    CF = 1 if a < b else 0
    ZF = 1 if result == 0 else 0
    SF = 1 if (result & sign_bit) != 0 else 0

    a_sign = 1 if (a & sign_bit) != 0 else 0
    b_sign = 1 if (b & sign_bit) != 0 else 0
    OF = 1 if (a_sign != b_sign) and (SF != a_sign) else 0

    PF = 1 if bin(result & 0xFF).count('1') % 2 == 0 else 0
    AF = 1 if (a & 0xF) < (b & 0xF) else 0

    return {'result': result, 'bits': bits,
            'CF': CF, 'ZF': ZF, 'SF': SF, 'OF': OF, 'PF': PF, 'AF': AF}


def show_flags(flags: dict, op_str: str):
    bits = flags['bits']
    r = flags['result']
    print(f"{op_str} → result={r} CF={flags['CF']} ZF={flags['ZF']} "
          f"SF={flags['SF']} OF={flags['OF']} PF={flags['PF']} AF={flags['AF']}")


def would_jump(instr: str, flags: dict) -> bool:
    CF, ZF, SF, OF, PF = flags['CF'], flags['ZF'], flags['SF'], flags['OF'], flags['PF']

    table = {
        'JE':  ZF == 1, 'JZ': ZF == 1,
        'JNE': ZF == 0, 'JNZ': ZF == 0,
        'JC':  CF == 1, 'JNC': CF == 0,
        'JS':  SF == 1, 'JNS': SF == 0,
        'JO':  OF == 1, 'JNO': OF == 0,
        'JP':  PF == 1, 'JNP': PF == 0,
        'JA':  CF == 0 and ZF == 0,
        'JAE': CF == 0, 'JNB': CF == 0,
        'JB':  CF == 1, 'JNAE': CF == 1,
        'JBE': CF == 1 or ZF == 1,
        'JNA': CF == 1 or ZF == 1,
        'JG':  ZF == 0 and SF == OF,
        'JGE': SF == OF,
        'JL':  SF != OF,
        'JLE': ZF == 1 or SF != OF,
    }
    return table.get(instr.upper(), False)


if __name__ == "__main__":
    f1 = compute_flags_add(100, 200)
    show_flags(f1, "ADD 100, 200")

    f2 = compute_flags_sub(10, 20)
    show_flags(f2, "CMP 10, 20")

    print("JG:", would_jump("JG", f2))
    print("JL:", would_jump("JL", f2))