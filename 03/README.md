> 本專案由 opencode 撰寫，部分對話摘要收錄於 [docs/record.md](docs/record.md)

# EmoLang 直譯器 v4.1

EmoLang 是一款結合 **C 語言結構**與 **Python 動態特性**的 Emoji 程式語言直譯器。

---

## 目錄結構

```
03/
├── emolang/                 # 主套件
│   ├── __init__.py
│   └── src/
│       ├── tokens.py        # Token 類型定義
│       ├── ast.py           # 抽象語法樹節點
│       ├── runtime.py       # 執行時期值類別
│       ├── lexer.py         # 詞法分析器
│       ├── parser.py        # 語法分析器
│       └── evaluator.py     # 執行引擎
├── emolang.py               # 主入口 (GUI + CLI + REPL)
├── emolang_lsp.py           # LSP 伺服器
├── tests/                   # EmoLang 測試程式 (.emo)
├── docs/
│   ├── record.md            # 開發記錄
│   ├── emoji-指令.md        # Emoji 指令參考
│   └── 使用指南.md          # GUI 功能指南
└── README.md                # 本檔案
```

---

## 前置需求

- Python 3.7+
- Tkinter（選用，用於 GUI 圖形介面；無 Tkinter 時自動使用終端機模式）

## 執行方式

### 1. 圖形介面模式 (GUI)
```bash
python emolang.py
```

### 2. 命令列模式 (CLI)
```bash
python emolang.py <檔案名稱>
```

### 3. 互動模式 (REPL)
```bash
python emolang.py -i
```

REPL 範例：

```text
>>> 📢 42
42
>>> 🛠️ add(a, b) 👇
...     🔙 a ➕ b
... 👆
>>> 📢 add(3, 4)
7
```

---

## 文件指南

| 文件 | 說明 |
|------|------|
| [docs/emoji-指令.md](docs/emoji-指令.md) | 完整 Emoji 指令參考與語法 |
| [docs/使用指南.md](docs/使用指南.md) | GUI 功能、快捷鍵、操作說明 |
| [docs/record.md](docs/record.md) | 開發歷程與版本變更記錄 |

---

## 直譯器流程

```
原始碼 (.emo)
  → 詞法分析 (lexer.py) → Token 串流
  → 語法分析 (parser.py) → AST 語法樹
  → 執行 (evaluator.py) → 輸出結果
```

---

## 授權

MIT License
