# EmoLang 直譯器 v4.0

EmoLang 是一款結合 **C 語言結構**與 **Python 動態特性**的 Emoji 程式語言直譯器。

---

## 目錄結構

```
03/
├── emolang/                 # 主套件資料夾
│   ├── __init__.py          # 套件初始化
│   └── src/                 # 原始碼模組
│       ├── __init__.py      # 模組初始化
│       ├── tokens.py        # Token 與 AST 類型定義
│       ├── ast.py           # 抽象語法樹節點
│       ├── runtime.py       # 執行時期值類別
│       ├── lexer.py         # 詞法分析器
│       ├── parser.py        # 語法分析器
│       └── evaluator.py     # 執行引擎
├── emolang.py               # 主程式入口 (GUI + CLI)
└── README.md                # 本檔案
```

---

## 安裝與執行

### 前置需求
- Python 3.7+
- Tkinter (選用，用於 GUI 圖形介面)

### 執行方式

#### 1. 圖形介面模式 (GUI)
```bash
python emolang.py
```
執行後會開啟圖形介面，包含：
- 程式碼編輯區
- 輸出結果區
- 新建/開啟/儲存/執行/清除按鈕

#### 2. 命令列模式 (CLI)
```bash
python emolang.py <檔案名稱>
```

#### 3. 互動模式
```bash
python emolang.py -i
```

---

## 直譯器架構

### 1. tokens.py - Token 類型定義

定義所有語法標記類型：

```python
class TokenType:
    TOK_LET      # 變數宣告 (📦🔢🎈📝🚦)
    TOK_ASSIGN   # 賦值 (🟰)
    TOK_IF       # 條件判斷 (🤔)
    TOK_ELSE     # 否則 (🤷)
    TOK_WHILE    # While 迴圈 (🔁)
    TOK_FOR      # For 迴圈 (🎡)
    TOK_PRINT    # 輸出 (📢)
    TOK_PLUS     # 加 (➕)
    TOK_MINUS    # 減 (➖)
    TOK_MUL      # 乘 (✖️)
    TOK_DIV      # 除 (➗)
    TOK_MOD      # 取餘 (✂️)
    TOK_EQ       # 等於 (🤝)
    TOK_GT       # 大於 (📈)
    TOK_LT       # 小於 (📉)
    # ... 更多
```

### 2. ast.py - 抽象語法樹

定義 AST 節點類型：

```python
class ASTType:
    AST_LET          # 變數宣告
    AST_ASSIGN       # 賦值
    AST_IF           # 條件判斷
    AST_WHILE        # While 迴圈
    AST_FOR          # For 迴圈
    AST_PRINT        # 輸出
    AST_BINOP        # 二元運算
    AST_NUM          # 數字
    AST_STR          # 字串
    AST_VAR          # 變數
    AST_FUNC_DEF     # 函數定義
    AST_FUNC_CALL    # 函數呼叫
    AST_RETURN       # 回傳
    # ... 更多
```

### 3. lexer.py - 詞法分析器

將源代碼字串切分成 Token 串流：

```python
class EmoLangLexer:
    def __init__(self, src):
        self.src = src           # 源代碼
        self.pos = 0            # 當前位置
        self.current_token = None

    def advance(self):
        # 跳過空白
        # 處理括號、逗號
        # 處理字串 (雙引號)
        # 處理數字 (整數/浮點數)
        # 處理 Emoji 關鍵字
        # 處理識別符 (變數名)
```

### 4. parser.py - 語法分析器

將 Token 組合成 AST（遞迴下降 parser）：

```python
class EmoLangParser:
    def parse(self):
        # 解析整個程式

    def parse_statement(self):
        # 解析敘述句 (函數、回傳、宣告、輸出、條件、迴圈)

    def parse_expression(self):
        # 解析表達式 (遞迴下降)
        # comparison -> addition -> factor -> prefix -> postfix -> primary
```

### 5. evaluator.py - 執行引擎

執行 AST 並管理虛擬記憶體：

```python
class EmoLangEvaluator:
    def reset(self):
        self.memory = {}        # 虛擬記憶體
        self.heap_ptr = 1       # 記憶體指標
        self.struct_table = {}  # 結構體表
        self.func_table = {}    # 函數表
        self.sym_stack = [{}]   # 符號堆疊

    def eval(self, node):
        # 求值表達式

    def execute(self, statements):
        # 執行敘述句

    def run(self, code):
        # 執行整個程式
```

---

## 執行流程

```
原始碼 (.emo)
     ↓
詞法分析 (lexer.py)
  Token 串流
     ↓
語法分析 (parser.py)
  AST 語法樹
     ↓
執行 (evaluator.py)
  輸出結果
```

---

## 開發指南

### 作為 Python 模組使用

```python
import sys
import os
sys.path.insert(0, os.path.join('emolang', 'src'))

from evaluator import EmoLangEvaluator

code = """
📝 x 🟰 10
📢 x
"""

interpreter = EmoLangEvaluator()
output = interpreter.run(code)
print(output)  # 輸出: 10
```

---

## 授權

MIT License