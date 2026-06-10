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

### 7. 加入 LSP 伺服器（已移除）

嘗試為 EmoLang 加入 Language Server Protocol 支援：

**實作的檔案：**
- `emolang_lsp.py`: LSP 伺服器（stdin/stdout JSON-RPC），支援 `textDocument/didOpen`、`textDocument/didChange`、`textDocument/semanticTokens/full`、`textDocument/hover`、`textDocument/documentSymbol`、`textDocument/completion`
- `test_lsp.py`: 28 項整合測試
- `tests/*.emo`: 5 個測試用 EmoLang 檔案

**修改的檔案：**
- `tokens.py`: Token 加入 `line`、`col`、`length` 欄位；新增 `tokenize()` 便利方法
- `lexer.py`: 加入位置追蹤（`self.line`、`self.col`）；匯入改為絕對路徑 `from emolang.src.tokens import ...`
- `parser.py`: 匯入改為絕對路徑 `from emolang.src.tokens import TokenType; from emolang.src.ast import ASTType, ASTNode`
- `evaluator.py`: 匯入改為絕對路徑 `from emolang.src.lexer import EmoLangLexer`

**關鍵決策：**
- LSP 伺服器為獨立程序（非內嵌於 GUI），可被任何 LSP 相容編輯器使用
- LSP 使用 0-based 行號（lexer 提供 1-based → 在 LSP 層減 1）
- I/O 使用 line-based header 解析 + `read(length)`，避免 pipe deadlock

**最終狀態：** 所有 LSP 相關檔案已移除，回復原始無 LSP 版本。

---

### 8. LSP 伺服器重新實作 + GUI/CLI 強化

重新加入 LSP 伺服器，參考 QiMing LSP 架構，並強化 GUI 與 CLI 功能。

**新增/修改的檔案：**
- `emolang_lsp.py`: LSP 伺服器（重新實作），新增 `highlight_ansi()` 與 ANSI 色碼
- `test_lsp.py`: 整合測試（7 項 28 子測試），新增 AST hover 測試與 range 驗證
- `emolang.py`: 加入 CLI REPL 模式（無 Tkinter 自動降級）、ANSI 語法突顯
- `emolang/src/ast.py`: ASTNode 新增 `line`、`col` 欄位
- `emolang/src/parser.py`: `create_node()` 記錄當前 token 位置
- `emolang/widgets.py`: 無變更
- `README.md`: 更新目錄結構與執行方式

**LSP 修正：**
- `_document_symbol`：range 從硬編碼 `{0,0}` 改為 AST 節點實際位置
- `_hover`：新增 `_find_ast_node_at()` AST 優先搜尋（雙層策略：AST → token fallback）

**GUI 修正：**
- `ScrolledText` 的 `tabs` 參數修正（`"    "` → `"1c"`，避免 Windows TclError）
- 語法突顯改用 Tcl/UCS-2 字元計數（`_tcl_col`、`_tcl_len`），修正 emoji surrogate pair 在 Windows Tcl/Tk 的位置偏移
- 語法突顯改為即時觸發（移除 200ms 延遲）
- emoji 工具列插入按鈕後立即套用突顯

**CLI 新增：**
- `run_repl()`：無 Tkinter 時自動啟動終端機 REPL，支援多行區塊與變數持久化
- `highlight_ansi()`：ANSI 終端機彩色輸出

**色彩配置：** VS Code Dark+ 風格
| 類別 | 顏色 | 用途 |
|------|------|------|
| keyword | `#c586c0` 紫色 | 📦📢🔁🤔🛠️👇👆 等 |
| variable | `#9cdcfe` 淺藍 | 變數名稱 |
| function | `#dcdcaa` 黃色 | 函式呼叫 |
| number | `#b5cea8` 綠色 | 數字常數 |
| string | `#ce9178` 橘色 | 字串 |
| operator | `#d69d85` 桃色 | 🟰➕➖✖️➗📈📉 等 |

---

### 9. 語法突顯重構 — 每個 emoji 獨立配色

將顏色系統從 `SEMANTIC_COLORS`（broad tag 分組）改為 `KEYWORD_COLORS` + `BASE_COLORS`，每個 emoji 指令有自己的 tag 與顏色。

**修改的檔案：**
- `emolang_lsp.py`: 新增 `KEYWORD_COLORS` dict（TokenType → 色碼）；`get_semantic_tag()` 改為回傳 `tok_xxx` 細粒度 tag；`TAG_COLORS` 合併 base + keyword 顏色；`encode_semantic_tokens()` 將細粒度 tag 對應回 broad category 供 LSP 使用；`highlight_ansi()` 同步轉換
- `emolang.py`: 匯入改為 `TAG_COLORS`；`SEMANTIC_TAG_MAP` 改由此建構
- TAB 插入建議後呼叫 `_apply_semantic_highlighting()`，修復幽靈文字無顏色的問題

**最終色彩配置：**

| Emoji | 色碼 | 類別 |
|-------|------|------|
| 📦🔢🎈📝🚦 | `#569cd6` 藍 | 變數宣告 |
| 🤔🤷 | `#c586c0` 紫 | 條件判斷 |
| 🔁🎡 | `#4ec9b0` 青綠 | 迴圈 |
| 📢📥 | `#dcdcaa` 黃 | 輸出/輸入 |
| 🛠️🔙 | `#cda869` 金黃 | 函式 |
| 🏗️ | `#cc7833` 橘褐 | 結構體 |
| 🆕 | `#6a8759` 深綠 | 建立實例 |
| 📋📖📚 | `#9876aa` 紫灰 | 資料結構 |
| 🛒📏 | `#6897bb` 灰藍 | 操作 |
| 🟢 | `#6a9955` 綠 | 真值 |
| 🔴 | `#f44747` 紅 | 假值 |
| 🟰➕➖✖️➗✂️🤝📈📉➡️📍🎯📌🔗🔀🙅 | `#d69d85` 桃色 | 運算子 |
| 變數識別字 | `#d4d4d4` 白 | 預設文字 |
| 數字 | `#b5cea8` 綠 | — |
| 字串 | `#ce9178` 橘 | — |

---

### 10. LSP 配色調整 + 大綱面板實作 (2026.06.09)

**配色調整：**
- 從每個 emoji 獨立配色改為 VS Code Dark+ C 語法慣例分組
- 控制流程 (🤔🤷🔁🎡🔙) → `#c586c0` 紫色
- 型別/宣告 (📦🔢🎈📝🚦🏗️🆕📋📖📚🟢🔴) → `#569cd6` 藍色
- 函式 (📢📥🛠️🛒📏) → `#dcdcaa` 黃色
- 移除 GUI 右上角 LSP 狀態標籤

**大綱面板 (左側)：**
- 新增 `📋 大綱` Listbox 於程式碼編輯區左側 (170px)
- 使用 `tk.Listbox` 搭配深色主題 (避免 `ttk.Treeview` 渲染問題)
- 遞迴解析 AST 顯示巢狀結構：
  - `🛠️ 函式` → 含參數 + 區域變數（縮排）
  - `🏗️ 結構` → 含成員變數（縮排）
  - `📦 變數` → 頂層宣告
- 點擊符號跳轉至對應行
- 使用 debounce (500ms) 避免頻繁解析
- 全部以 `try/except` 包裹，不影響其他功能

**修改的檔案：**
- `emolang_lsp.py`: `KEYWORD_COLORS` 改為 VS Code Dark+ C 分組配色
- `emolang.py`: 重新實作大綱面板 (`_schedule_outline_update`, `_do_update_outline`, `_add_outline_node`, `_on_outline_select`)、匯入 `EmoLangLexer`/`EmoLangParser`、`code_label`/`code_text` 從 `pack` 改為 `grid`（容納大綱左欄）

---

### 11. 語法突顯修正 + Emoji 字型修復 (2026.06.10)

**問題回報：**
1. 字串結尾引號和前一個字元是預設白色，未套用 LSP 字串顏色 (`#ce9178`)
2. 引號內的表情符號顯示為方框加問號

**Bug 分析：**
- `_apply_semantic_highlighting()` 使用 `_tcl_len(tok.value)` 計算 Tcl 寬度，但 `tok.value` 不包含引號，導致結尾 `"` 不在 tag 範圍內
- 缺字問題：編輯器字型 `Consolas` 不含 emoji glyph

**修改的檔案：**
- `emolang.py`:
  - `_apply_semantic_highlighting()`: 改為從原始碼行取 `line_text[tok.col-1 : tok.col-1+tok.char_length]` 計算正確 Tcl 範圍
  - `_find_token_at()`: 同上修正 hover 偵測範圍
  - `on_mouse_move()`: 同上修正 hover underline 範圍
  - `EmoLangGUI.__init__`: 新增 `tkinter.font.Font` 物件，加入 `Segoe UI Emoji` fallback 字型
  - `code_text` / `output_text`: 改用新字型物件
  - `GhostText`: 傳入 `self.editor_font`
- `emolang/widgets.py`:
  - `GhostText.__init__`: 新增 `font` 參數，預設保留 `("Consolas", 11)`
  - `GhostText.show`: 使用自訂字型

**LSP 未完成功能清單（依建議實作順序）：**
1. diagnostics — 語法錯誤診斷 (`publishDiagnostics`)
2. didClose / didSave — 文件生命週期補完
3. go to definition — 跳至定義
4. find references — 尋找引用
5. rename — 重新命名符號
6. foldingRange — 程式碼折疊
7. signatureHelp — 函式參數提示
8. formatting — 自動排版
9. codeAction — 快速修復

---