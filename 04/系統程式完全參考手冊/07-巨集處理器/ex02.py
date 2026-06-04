# ============================================================
#  第 7 章　習題 02 — C 前置處理器巨集模擬器
#  實作：模擬 #define 的物件式與函式式巨集展開、
#        括號保護規則、#ifdef 條件編譯、__VA_ARGS__ 可變引數
# ============================================================

import re


class CPreprocessor:
    """
    模擬 C 前置處理器（cpp）的核心行為：
    - 物件式巨集展開（#define NAME value）
    - 函式式巨集展開（#define FUNC(a,b) ...）
    - 條件編譯（#ifdef / #ifndef / #else / #endif）
    - 展開結果追蹤
    """

    def __init__(self):
        self.defines: dict[str, tuple] = {}   # name → (params, body)
        self.log: list[str] = []

    def define(self, name: str, body: str, params: list[str] | None = None):
        """登記一個 #define"""
        self.defines[name] = (params, body)

    def undef(self, name: str):
        """#undef"""
        self.defines.pop(name, None)

    def is_defined(self, name: str) -> bool:
        return name in self.defines

    def expand(self, text: str, depth: int = 0) -> str:
        """
        展開 text 中所有已知的巨集（含遞迴展開）。
        depth 用於防止無限遞迴（最多 10 層）。
        """
        if depth > 10:
            return text

        result = text
        changed = True
        while changed:
            changed = False
            for name, (params, body) in self.defines.items():
                if params is None:
                    # 物件式：直接替換所有 token
                    pattern = r'\b' + re.escape(name) + r'\b'
                    new_result = re.sub(pattern, body, result)
                    if new_result != result:
                        result  = new_result
                        changed = True
                else:
                    # 函式式：搜尋 NAME(arg1, arg2, ...)
                    pattern = re.escape(name) + r'\s*\(([^)]*)\)'
                    def replacer(m):
                        args_str = m.group(1)
                        args     = [a.strip() for a in args_str.split(',')]
                        b        = body
                        if '...' in params:
                            # __VA_ARGS__ 支援
                            fixed = [p for p in params if p != '...']
                            for i, p in enumerate(fixed):
                                b = re.sub(r'\b' + re.escape(p) + r'\b',
                                           args[i] if i < len(args) else '', b)
                            va_args = ', '.join(args[len(fixed):])
                            b = b.replace('__VA_ARGS__', va_args)
                            # ## 前置刪除多餘逗號
                            b = re.sub(r',\s*##\s*', lambda m2: '' if not va_args else ', ', b)
                        else:
                            for p, a in zip(params, args):
                                b = re.sub(r'\b' + re.escape(p) + r'\b', a, b)
                        return b
                    new_result = re.sub(pattern, replacer, result)
                    if new_result != result:
                        result  = new_result
                        changed = True
        return result

    def process_source(self, source: str) -> list[tuple[str, str]]:
        """
        處理一段 C 原始碼（逐行），處理 #define/#ifdef 等，
        回傳 [(原始行, 展開後)] 的列表
        """
        output = []
        lines  = source.strip().splitlines()
        skip_stack = []   # 條件編譯的堆疊
        i = 0

        while i < len(lines):
            raw  = lines[i]
            line = raw.strip()

            # 判斷是否在 skip 區域
            skipping = any(s for s in skip_stack)

            if line.startswith('#define'):
                if not skipping:
                    self._parse_define(line)
                    output.append((raw, '（已登記至巨集定義表）'))
            elif line.startswith('#undef'):
                if not skipping:
                    name = line.split()[1]
                    self.undef(name)
                    output.append((raw, f'（已移除 {name}）'))
            elif line.startswith('#ifdef'):
                name = line.split()[1]
                skip_stack.append(not self.is_defined(name))
                output.append((raw, f'{"展開" if not skip_stack[-1] else "跳過"} 此區塊'))
            elif line.startswith('#ifndef'):
                name = line.split()[1]
                skip_stack.append(self.is_defined(name))
                output.append((raw, f'{"展開" if not skip_stack[-1] else "跳過"} 此區塊'))
            elif line.startswith('#else'):
                if skip_stack:
                    skip_stack[-1] = not skip_stack[-1]
                output.append((raw, '切換條件'))
            elif line.startswith('#endif'):
                if skip_stack:
                    skip_stack.pop()
                output.append((raw, '結束條件區塊'))
            elif line.startswith('#'):
                output.append((raw, '（其他指令）'))
            elif line == '' or line.startswith('//'):
                output.append((raw, raw))
            else:
                if not skipping:
                    expanded = self.expand(line)
                    output.append((raw, expanded))
                else:
                    output.append((raw, '（跳過）'))
            i += 1

        return output

    def _parse_define(self, line: str):
        """解析 #define 行，登記到 self.defines"""
        # 移除 #define
        rest = line[len('#define'):].strip()
        # 函式式巨集：NAME(params) body
        m = re.match(r'(\w+)\(([^)]*)\)\s*(.*)', rest)
        if m:
            name   = m.group(1)
            params = [p.strip() for p in m.group(2).split(',')]
            body   = m.group(3)
            self.define(name, body, params)
        else:
            # 物件式：NAME body
            parts = rest.split(None, 1)
            name  = parts[0]
            body  = parts[1] if len(parts) > 1 else ''
            self.define(name, body)


# ── 示範 ──────────────────────────────────────────────────────

def demo_object_macros():
    print("=" * 65)
    print("  示範 1：物件式巨集展開")
    print("=" * 65)

    cpp = CPreprocessor()
    source = """\
#define PI 3.14159265
#define MAX_SIZE 1024
#define NEWLINE_CHAR '\\n'
#define TRUE 1
#define FALSE 0

double area = PI * r * r;
int buf[MAX_SIZE];
int flag = TRUE;
if (flag == FALSE) return;
"""
    result = cpp.process_source(source)
    print(f"\n  {'原始碼':<40}  →  展開結果")
    print(f"  {'─'*72}")
    for orig, exp in result:
        if orig.strip() and not orig.strip().startswith('#'):
            print(f"  {orig.strip():<40}  →  {exp}")


def demo_function_macros():
    print("\n" + "=" * 65)
    print("  示範 2：函式式巨集（括號保護）")
    print("=" * 65)

    cpp = CPreprocessor()

    # 危險版本（未加括號）
    cpp.define('BAD_SQUARE', 'x * x', ['x'])
    # 安全版本
    cpp.define('SQUARE',     '((x) * (x))', ['x'])
    cpp.define('MAX',        '((a) > (b) ? (a) : (b))', ['a', 'b'])
    cpp.define('ABS',        '((x) < 0 ? -(x) : (x))', ['x'])
    cpp.define('ARRAY_SIZE', '(sizeof(arr) / sizeof((arr)[0]))', ['arr'])

    cases = [
        ("BAD_SQUARE(1 + 2)",   "BAD_SQUARE(1 + 2)"),
        ("SQUARE(1 + 2)",       "SQUARE(1 + 2)"),
        ("MAX(a, b + 1)",       "MAX(a, b + 1)"),
        ("ABS(-5)",             "ABS(-5)"),
        ("ABS(x - 10)",         "ABS(x - 10)"),
        ("ARRAY_SIZE(my_arr)",  "ARRAY_SIZE(my_arr)"),
    ]

    print(f"\n  {'巨集呼叫':<28}  {'展開結果'}")
    print(f"  {'─'*65}")
    for desc, call in cases:
        expanded = cpp.expand(call)
        print(f"  {call:<28}  →  {expanded}")

    print(f"""
  ★ 括號保護的重要性：
    BAD_SQUARE(1+2) → 1+2 * 1+2 = 1+2+2 = 5  ← 錯誤！
    SQUARE(1+2)     → ((1+2) * (1+2)) = 9      ← 正確
""")


def demo_multiline_macros():
    print("=" * 65)
    print("  示範 3：多行巨集與 do-while(0) 慣用法")
    print("=" * 65)

    print(r"""
  問題：直接用 { } 的巨集在 if-else 中會有語法問題

  #define BAD_SWAP(a, b) { int t=a; a=b; b=t; }

  if (cond)
      BAD_SWAP(x, y);   → if (cond) { int t=x; x=y; y=t; };
  else                                                       ↑ 多餘分號
      ...               → ❌ else 前出現孤立的分號，編譯錯誤！

  ─────────────────────────────────────────────────

  解決：用 do { ... } while(0) 包裝

  #define SWAP(a, b) do { int t=(a); (a)=(b); (b)=t; } while(0)

  if (cond)
      SWAP(x, y);   → if (cond) do { int t=(x); (x)=(y); (y)=t; } while(0);
  else              →                                              ↑ 分號屬於 while(0)
      ...           → ✓ else 正常接上

  do-while(0) 的特性：
    1. 整個巨集被視為「一個語句」（與普通函式呼叫一致）
    2. 結尾的分號有正確的語義位置
    3. 內部的區域變數 t 有自己的作用域
    4. while(0) 保證不重複執行（編譯器會最佳化掉）
""")

    # 模擬展開
    cpp = CPreprocessor()
    # 簡化版（不處理多行，只示意）
    cpp.define('SWAP',
               'do { int _t=(a); (a)=(b); (b)=_t; } while(0)',
               ['a', 'b'])

    cases = [
        "SWAP(x, y)",
        "SWAP(arr[i], arr[j])",
        "SWAP(*p, *q)",
    ]

    print(f"  {'呼叫':<24}  →  展開結果")
    print(f"  {'─'*70}")
    for c in cases:
        print(f"  {c:<24}  →  {cpp.expand(c)}")


def demo_conditional_compilation():
    print("\n" + "=" * 65)
    print("  示範 4：條件編譯（#ifdef / #ifndef）")
    print("=" * 65)

    source = """\
#define DEBUG_MODE
#define PLATFORM_LINUX

#ifdef DEBUG_MODE
int debug_level = 3;
#else
int debug_level = 0;
#endif

#ifdef PLATFORM_LINUX
#define SLEEP_MS(ms) usleep((ms)*1000)
#endif

#ifndef RELEASE_BUILD
int x = 0xDEAD;
#endif

SLEEP_MS(100);
"""
    cpp = CPreprocessor()
    result = cpp.process_source(source)

    print(f"\n  {'原始碼':<35}  {'說明 / 展開'}")
    print(f"  {'─'*72}")
    for orig, exp in result:
        o = orig.strip()
        if not o:
            continue
        marker = "→" if not o.startswith('#') else " "
        print(f"  {o:<35} {marker} {exp}")


def demo_va_args():
    print("\n" + "=" * 65)
    print("  示範 5：可變引數巨集（__VA_ARGS__）")
    print("=" * 65)

    print(r"""
  C99 引入 __VA_ARGS__，讓巨集可接受不定數量的額外引數：

  #define LOG(level, fmt, ...) \
      fprintf(stderr, "[%s] " fmt "\n", level, ##__VA_ARGS__)

  ##__VA_ARGS__ 的 ## 前綴：
    - 若 ... 部分為空，自動刪除前面的逗號
    - 避免 LOG("INFO", "ready") 展開成 fprintf(..., "INFO", "ready",)（多餘逗號）
""")

    cpp = CPreprocessor()
    # 簡化版（單行，無 ## 前綴處理，僅示意）
    cpp.define('LOG',
               'fprintf(stderr, "[%s] " fmt "\\n", level, __VA_ARGS__)',
               ['level', 'fmt', '...'])

    cases = [
        ('LOG("INFO", "started")',              '"INFO", "started"'),
        ('LOG("ERROR", "val=%d", x)',           '"ERROR", "val=%d", x'),
        ('LOG("WARN",  "a=%d b=%d", a, b)',     '"WARN",  "a=%d b=%d", a, b'),
    ]

    print(f"  {'原始呼叫':<45}  展開結果（簡化）")
    print(f"  {'─'*72}")
    for call, _ in cases:
        expanded = cpp.expand(call)
        print(f"  {call:<45}")
        print(f"    → {expanded}\n")

    print(r"""
  預定義巨集（常用）：
    __FILE__  : 目前原始檔名（字串字面值）
    __LINE__  : 目前行號（整數）
    __func__  : 目前函式名（C99，字串）
    __DATE__  : 編譯日期
    __TIME__  : 編譯時間

  應用：
  #define ASSERT(cond) \
      do { if (!(cond)) { \
          fprintf(stderr, "ASSERT 失敗：%s  檔案：%s  行：%d\n", \
                  #cond, __FILE__, __LINE__); \
          abort(); \
      } } while(0)

  ASSERT(x > 0);
  // 若 x <= 0：ASSERT 失敗：x > 0  檔案：main.c  行：42
""")


if __name__ == "__main__":
    demo_object_macros()
    demo_function_macros()
    demo_multiline_macros()
    demo_conditional_compilation()
    demo_va_args()