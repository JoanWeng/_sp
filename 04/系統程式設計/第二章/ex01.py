# ============================================================
#  第 2 章　習題 01 — 位置計數器（Location Counter）模擬器
#  實作：模擬組譯器第一遍掃描，追蹤 LC 並記錄每個變數的位址
# ============================================================

# 每種虛擬指令對應的 byte 大小
DIRECTIVE_SIZE = {
    'DB': 1,
    'DW': 2,
    'DD': 4,
    'DQ': 8,
    'DT': 10,
}

def parse_operand_count(operand_str):
    """計算運算元中有幾個元素（逗號分隔），用於陣列定義"""
    return len(operand_str.split(','))

def location_counter_sim(data_definitions, start=0):
    """
    模擬 .data 區段的位置計數器。

    輸入格式：
        data_definitions = [
            ('標號', '虛擬指令', '運算元字串'),
            ...
        ]
        若為 RESB/RESW/RESD/RESQ，運算元直接為整數保留數量。

    回傳：
        list of dict，每項包含 label, directive, size, address
    """
    results = []
    lc = start

    for label, directive, operand in data_definitions:
        directive = directive.upper()

        # 計算大小
        if directive == 'RESB':
            size = int(operand)
        elif directive == 'RESW':
            size = int(operand) * 2
        elif directive == 'RESD':
            size = int(operand) * 4
        elif directive == 'RESQ':
            size = int(operand) * 8
        elif directive == 'DB' and operand.startswith('"'):
            # 字串定義：去掉引號後取長度
            inner = operand.strip('"')
            size = len(inner)
        elif directive in DIRECTIVE_SIZE:
            unit = DIRECTIVE_SIZE[directive]
            count = parse_operand_count(operand)
            size = unit * count
        else:
            size = 0

        results.append({
            'label':     label,
            'directive': directive,
            'operand':   operand,
            'size':      size,
            'address':   lc,
        })
        lc += size

    return results, lc  # lc 最終值 = 總大小


def main():
    print("=" * 60)
    print("  位置計數器（Location Counter）模擬器")
    print("=" * 60)

    # 模擬以下 NASM .data 區段：
    #   msg      DB  "Hello, World!"
    #   newline  DB  0x0a
    #   count    DD  0
    #   flags    DB  1, 0, 1, 0
    #   buffer   RESB 64
    #   matrix   RESD 9        ; 3x3 整數矩陣

    data_section = [
        ('msg',     'DB',   '"Hello, World!"'),
        ('newline', 'DB',   '0x0a'),
        ('count',   'DD',   '0'),
        ('flags',   'DB',   '1, 0, 1, 0'),
        ('buffer',  'RESB', '64'),
        ('matrix',  'RESD', '9'),
    ]

    results, total = location_counter_sim(data_section)

    # 輸出結果表格
    print(f"\n{'標號':<12} {'虛擬指令':<8} {'運算元':<20} {'大小(bytes)':<12} {'位址(hex)'}")
    print("-" * 65)
    for r in results:
        print(f"{r['label']:<12} {r['directive']:<8} {r['operand']:<20} "
              f"{r['size']:<12} 0x{r['address']:04X}")

    print("-" * 65)
    print(f"{'[.data 區段總大小]':<42} {total} bytes")

    # 進一步驗證：印出每個標號的位址
    print("\n符號表（Symbol Table）：")
    for r in results:
        print(f"  {r['label']:<12} → 0x{r['address']:04X}  ({r['address']} dec)")

    # 示範 EQU 等效計算
    print("\nEQU 等效計算：")
    msg_entry = next(r for r in results if r['label'] == 'msg')
    print(f"  msg_len  EQU $ - msg  →  {msg_entry['size']} bytes")
    matrix_entry = next(r for r in results if r['label'] == 'matrix')
    print(f"  mat_len  EQU $ - matrix  →  {matrix_entry['size']} bytes  ({matrix_entry['size']//4} 個 DWORD)")


if __name__ == '__main__':
    main()