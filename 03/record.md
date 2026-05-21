# EmoLang 直譯器開發記錄

---

## 2024 工作紀錄

### 1. 模組拆分

將單一 `emolang.py` 拆分為多個程式模組：

```
03/
├── emolang/                 # 主套件資料夾
│   ├── __init__.py
│   └── src/                 # 原始碼模組
│       ├── __init__.py
│       ├── tokens.py        # Token 與 AST 類型定義
│       ├── ast.py           # 抽象語法樹節點
│       ├── runtime.py       # 執行時期值類別
│       ├── lexer.py         # 詞法分析器
│       ├── parser.py        # 語法分析器
│       └── evaluator.py     # 執行引擎
├── emolang.py               # 主程式入口 (GUI + CLI)
├── README.md                # 使用說明 + 架構
└── commands.md             # 指令總覽
```

**執行方式：**
- `python emolang.py` - 啟動 GUI
- `python emolang.py <file.emo>` - 執行檔案
- `python emolang.py -i` - 互動模式

---

### 2. 新增邏輯運算子 (AND, OR, NOT)

從 02 目錄的 C 語言版本移植邏輯運算功能：

| Emoji | 指令 | 說明 |
|-------|------|------|
| 🔗 | AND | 邏輯 AND (短路求值) |
| 🔀 | OR | 邏輯 OR (短路求值) |
| 🙅 | NOT | 邏輯 NOT |

**修改的檔案：**
- `tokens.py`: 新增 `TOK_AND`, `TOK_OR`, `TOK_NOT`
- `ast.py`: 新增 `AST_NOT`
- `lexer.py`: 新增關鍵字映射 🔗, 🔀, 🙅
- `parser.py`: 新增 `parse_logical_and()` 處理 AND，更新 `parse_expression()` 處理 OR，在 `parse_prefix()` 處理 NOT
- `evaluator.py`: 新增 AST_NOT 運算處理，以及 AND/OR 的短路求值邏輯
- `commands.md`: 新增邏輯運算說明

**測試範例：**
```
📝 a 🟰 🟢
📝 b 🟰 🔴
📢 a 🔗 b   # 輸出: 0
📢 a 🔀 b   # 輸出: 1
📢 🙅 a    # 輸出: 0
📢 🙅 b    # 輸出: 1
```

---

### 3. README.md 更新

重寫為繁體中文，包含：
- 目錄結構
- 安裝與執行方式
- 直譯器架構說明
- 執行流程
- 開發指南
- 授權資訊

---

### 4. commands.md 指令總覽

新增完整指令說明文件，包含：
- 變數宣告與賦值
- 輸出/輸入
- 條件判斷與迴圈
- 運算子（算術、比較、邏輯）
- 布林值
- 函數
- 結構體
- 指標與記憶體
- 陣列
- 優先順序

---

### 5. 嘗試語法高亮（已移除）

曾嘗試在 GUI 加入語法高亮功能，但因為：
- 覆蓋文字顏色導致 emoji 失去原本彩色
- 部分 emoji 無法正常顯示

最終決定移除此功能，保持 Tkinter 預設的文字顯示。

---

## 檔案變更清單

| 檔案 | 變更說明 |
|------|----------|
| `emolang.py` | 主程式入口，保持不變 |
| `emolang/__init__.py` | 新增套件初始化 |
| `emolang/src/__init__.py` | 新增模組初始化 |
| `emolang/src/tokens.py` | 新增 AND, OR, NOT Token |
| `emolang/src/ast.py` | 新增 AST_NOT 節點類型 |
| `emolang/src/lexer.py` | 新增 🔗 🔀 🙅 關鍵字 |
| `emolang/src/parser.py` | 新增邏輯運算解析 |
| `emolang/src/evaluator.py` | 新增短路求值執行 |
| `README.md` | 重寫為繁體中文 |
| `commands.md` | 新增指令總覽文件 |

---

### 6. 新增列表 (List) 與字典 (Dictionary) 支援

從 02 目錄的 C 語言版本移植列表/字典功能：

| Emoji | 指令 | 說明 |
|-------|------|------|
| 📋 | LIST | `🆕 📋` (建立列表) |
| 📖 | DICT | `🆕 📖` (建立字典) |
| 🛒 | APPEND | `list 🛒 值` (追加元素) |
| 📏 | LEN | `📏 obj` (長度) |

**修改的檔案：**
- `tokens.py`: 新增 `TOK_LIST`, `TOK_DICT`, `TOK_APPEND`, `TOK_LEN`
- `ast.py`: 新增 `AST_NEW_LIST`, `AST_NEW_DICT`, `AST_APPEND`, `AST_LEN`
- `lexer.py`: 新增關鍵字映射 📋, 📖, 🛒, 📏
- `parser.py`: 重構 `parse_prefix` → `parse_prefix_only` + 後綴包裝以修正 `🎯` 與 `➡️` 的優先級順序；新增 APPEND 語句處理
- `evaluator.py`: 新增 `list_pool`/`dict_pool`、`assign_value`（支援列表/字典索引賦值）、`dict_set`/`dict_get`、漂亮輸出列表 `[a, b]` 與字典 `{"k": v}`
- `README.md`: 更新 Token/AST/Evaluator 說明
- `commands.md`: 新增列表與字典指令

**修復的 Bug：** 解析器優先級 — `🎯 ptr ➡️ 攻擊力` 原解析為 `DEREF(DOT(VAR, field))`（02 C 版本亦有此錯誤），修正為 `DOT(DEREF(VAR), field)`，使指標 + 結構體欄位賦值能正確運作。

**測試範例：**
```
📦 items 🟰 🆕 📋
items 🛒 "蘋果"
📢 items              # 輸出: ["蘋果"]

📦 player 🟰 🆕 📖
player📌"hp" 🟰 100
📢 player            # 輸出: {"hp": 100}
📢 📏 player         # 輸出: 1
```

---