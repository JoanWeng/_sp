import os

try:
    import tkinter as tk  # noqa: F401
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

if HAS_TKINTER:
    from emolang_lsp import TAG_COLORS
    SEMANTIC_TAG_MAP = {name: {"fg": color} for name, color in TAG_COLORS.items()}
else:
    SEMANTIC_TAG_MAP = {}

EMOJI_NAMES = {
    "📦": "LET 通用變數（void*，可裝載任何型態）",
    "🔢": "INT 整數變數（int）",
    "🎈": "FLOAT 小數變數（float）",
    "📝": "STR 字串變數（str）",
    "🚦": "BOOL 布林變數（bool）",
    "🟰": "ASSIGN 賦值（=）",
    "📢": "PRINT 輸出值到畫面",
    "📥": "INPUT 讀取使用者輸入",
    "🤔": "IF 條件判斷",
    "🤷": "ELSE 否則分支",
    "🔁": "WHILE 條件迴圈",
    "🎡": "FOR 計數迴圈",
    "🚧": "SEP For 迴圈分隔符",
    "👇": "LBRACE 區塊開始 {",
    "👆": "RBRACE 區塊結束 }",
    "🛠": "FUNC 定義函數",
    "🔙": "RETURN 從函數回傳值",
    "🏗️": "STRUCT 定義結構體",
    "🆕": "NEW 建立實例（struct/list/dict）",
    "➡️": "DOT 存取成員欄位（obj.field）",
    "➕": "PLUS 加法或字串拼接（+）",
    "➖": "MINUS 減法（-）",
    "✖️": "MUL 乘法（*）",
    "➗": "DIV 除法（/）",
    "✂️": "MOD 取餘數（%）",
    "🤝": "EQ 等於比較（==）",
    "📈": "GT 大於（>）",
    "📉": "LT 小於（<）",
    "🔗": "AND 邏輯 AND（&&）",
    "🔀": "OR 邏輯 OR（||）",
    "🙅": "NOT 邏輯 NOT（!）",
    "📍": "REF 取變數位址（&）",
    "🎯": "DEREF 解參考取得值（*）",
    "📌": "INDEX 索引存取（arr[i]）",
    "📚": "ARRAY 配置連續記憶體",
    "📋": "LIST 建立空白列表",
    "📖": "DICT 建立空白字典",
    "🛒": "APPEND 追加元素到列表尾端",
    "📏": "LEN 計算長度",
    "🟢": "TRUE 真值（1）",
    "🔴": "FALSE 假值（0）",
}

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMOJI_KEY_CONFIG_FILE = os.path.join(_PROJECT_ROOT, "emoji_keys.json")

DEFAULT_EMOJI_KEY_MAP = {
    'a': '📦', 'b': '📢', 'c': '🤔', 'd': '🔁', 'e': '📝',
    'f': '🛠', 'g': '🏗️', 'h': '👇', 'i': '📥', 'j': '👆',
    'k': '🔙', 'l': '📖', 'm': '➕', 'n': '🆕', 'o': '🔀',
    'p': '✖️', 'q': '🤷', 'r': '➡️', 's': '🙅', 't': '🟰',
    'u': '🎡', 'v': '🎯', 'w': '📈', 'x': '➖', 'y': '🤝',
    'z': '📉',
}
