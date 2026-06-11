# EmoLang 直譯器開發記錄  

> ⚠️ **注意**：本文件由 AI 輔助維護，記錄可能不完整。

---

## 工作紀錄

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

---

### 12. 程式碼摺疊、重新命名、參考查詢、行號 (2026.06.10)

**新增功能：**

| 功能 | 觸發方式 | 說明 |
|------|----------|------|
| 全部摺疊 | 工具列 `🔽` 按鈕 | 將所有頂層區塊（函數/if/else/for/while/struct 主體）摺疊為一行標記 |
| 全部展開 | 工具列 `🔼` 按鈕 | 展開所有已摺疊區塊 |
| 單擊展開 | 點擊摺疊標記 | 點擊 `  … 👆 (N lines) [#XXXX]  ` 即可展開該區塊 |
| 重新命名 | `F2` | 將檔案內所有同名的識別字重新命名 |
| 查詢參考 | `Ctrl+Shift+F` | 彈出視窗顯示所有參考位置，點擊跳轉 |
| 跳至定義 | `F12` / `Ctrl+G` | 游標跳到該符號的定義位置 |
| 行號 | 編輯器左側 | 即時更新的行號，隨摺疊/展開自動同步 |

**實作細節：**

- **摺疊機制：** `_get_folding_ranges()` 回傳僅頂層 `{ … }` 配對範圍（brace stack 歸零才算）。`_fold_all()` 從最底部開始反向刪除（`reverse=True`），每區塊替換成唯一標記 `  … 👆 (N lines) [#uid]  \n`，其中 `uid = id(text) & 0xFFFF`。`_folded_regions` 儲存 `(原始文字, 標記文字)` 元組串列。
- **展開機制：** `_unfold_all()` 使用 `search(marker, tk.END, backwards=True)` 從文件底部往回找每個標記並還原。`_unfold_marker_at_line()` 使用 `search(marker, f"{line}.0", f"{line+1}.0")` 在指定行範圍內尋找。
- **摺疊標記點擊：** `fold_marker` tag 綁定 `<Button-1>` → `_on_fold_click` 取得點擊行號 → `_unfold_marker_at_line`。
- **重新命名：** `_get_all_id_tokens()` 收集檔案中所有 `TOK_ID` token，按值分組。`_rename_symbol` 先展開所有摺疊區塊，再從最後一處開始反向取代（避免行號位移）。
- **參考查詢：** 同上收集 ID token，在彈出視窗 `tk.Listbox` 中列出，點擊跳轉。
- **跳至定義：** `_get_def_map()` 解析 AST 取得 `LET` / `FUNC_DEF` 節點的定義 token，`_go_to_definition` 搜尋該名稱在定義行的第一個出現位置。
- **行號：** `ScrolledText` 改為 `tk.Text` + 自訂 `Scrollbar`。左側 `line_numbers` Text widget（寬度 6，唯讀）與 `code_text` 共用同一 scrollbar，透過 `yview` 和 `_on_code_mousewheel` 同步。`_update_line_numbers()` 計算 `code_text` 總行數並寫入。

**Bug 修復：**

1. `tag_configure` font 參數格式錯誤：傳入 `("Consolas", 11)` 而非 `self.editor_font` → 修正為直接傳入字型物件。
2. 雙重點擊摺疊按鈕導致 region 丟失：`_fold_all()` 開頭檢查 `self._folded_regions` 若非空則直接返回。
3. 嵌入式視窗方案引發 AttributeError：改用純文字標記 + `search()`。
4. 連續相同層級區塊（如 `if/else if/else`）摺疊標記文字相同導致 `search()` 誤配：每個標記加入唯一 `[#XXXX]` hex ID。
5. 展開時錯亂：`search(marker, tk.END, backwards=True)` 確保從底部往回匹配，還原後程式碼順序正確。
6. `mark_gravity` 參數類型錯誤：`tk.LEFT` → `"left"`。
7. `state='disabled'` 凍結編輯器：改用 `state='normal'` 搭配唯讀 line_numbers widget。

**修改的檔案：**
- `emolang.py`: 新增 `_get_folding_ranges`, `_fold_all`, `_unfold_all`, `_unfold_marker_at_line`, `_on_fold_click`, `_get_all_id_tokens`, `_show_references`, `_rename_symbol`, `_get_def_map`, `_go_to_definition`, `_update_line_numbers`, `_sync_line_numbers_scroll`, `_on_code_scroll`, `_on_code_mousewheel`；編輯區從 `ScrolledText` 改為 `tk.Text + Scrollbar`；`new_file` / `open_file` / `insert_emoji` / `on_key_release` 加入 `_update_line_numbers()` 呼叫
- `emolang_lsp.py`: 無變更
- `test_lsp.py`: 無變更

---

### 13. 診斷修復 — 空字串誤報與行號偏移問題 (2026.06.11)

**問題回報：**
1. `""`（空字串）作為 bare expression 時被錯誤標記為「少了 📢」
2. 新增/刪除行數後，診斷器產生錯誤的語法判斷（如 `📢` 後接換行導致 EOF 行號錯誤）

**Bug 分析：**
- **空字串誤報**：`_BARE_EXPR_TYPES` 包含 `AST_STR`，導致所有 bare 字串表達式（含 `""`）都被標記為「少了 📢」。但空字串是合法的表達式值，不應視為語法錯誤。
- **行號偏移**：`_diag_parse_statement` 中 `create_node()` 從 `self.lexer.current_token` 取得行號，但該行號在關鍵字被 consume 後指向了下一個 token 或 EOF，導致錯誤標記在錯行。
- **缺少表達式保護**：`📢`、`📦 🟰`、`🤔`、`🔁`、`🔙` 等關鍵字後直接呼叫 `parse_expression()`，若當前 token 為 EOF 則拋出 `RuntimeError("解析表達式出錯")`，該錯誤被主循環捕獲時已無正確行號資訊。

**修改的檔案：**
- `emolang/src/parser.py`:

  **`_BARE_EXPR_TYPES`**：
  - 移除 `ASTType.AST_STR`，僅保留 `AST_NUM`、`AST_FLOAT`、`AST_TRUE`、`AST_FALSE`

  **`_diag_parse_statement`（診斷解析器）**：
  - `TOK_RETURN`、`TOK_LET`、`TOK_PRINT`、`TOK_IF`、`TOK_WHILE`：在 `advance()` 前暫存關鍵字行號，`create_node()` 後覆蓋為關鍵字行號
  - `TOK_LET`：`🟰` 後加入 `_EXPR_STARTERS` 檢查，若無表達式則報「語法錯誤: 🟰 後缺少表達式」
  - `TOK_PRINT`：加入 `_EXPR_STARTERS` 檢查，若無表達式則報「語法錯誤: 📢 後缺少表達式」而非拋出未知錯誤
  - `TOK_RETURN`：加入 `_EXPR_STARTERS` 檢查，若無表達式則報「語法錯誤: 🔙 後缺少表達式」
  - `TOK_IF`：加入 `_EXPR_STARTERS` 檢查，若無表達式則報「語法錯誤: 🤔 後缺少條件表達式」
  - `TOK_WHILE`：加入 `_EXPR_STARTERS` 檢查，若無表達式則報「語法錯誤: 🔁 後缺少條件表達式」

**影響範圍：**
- `_BARE_EXPR_TYPES` 變更影響：診斷器與非診斷解析器的「少了 📢」判斷。`""`、`"字串"` 等字串表達式不再被標記。數字 (`42`)、小數 (`3.14`)、布林 (`🟢`/`🔴`) 仍會被標記。
- `node.line` 變更影響：大綱面板跳轉、錯誤標記行、定義跳轉，現在指向關鍵字行而非變數名/表達式行。
- 所有診斷錯誤均有對應的、不拋異常的描述。

**最終檔案狀態（差分摘要）：**

| 區塊 | 變更 |
|------|------|
| `_BARE_EXPR_TYPES` | `AST_STR` 移除 |
| `TOK_RETURN` 分支 | 行號快取 + 表達式守衛 |
| `TOK_LET` 分支 | 行號快取 + 🟰 後表達式守衛 |
| `TOK_PRINT` 分支 | 行號快取 + 表達式守衛 + 缺少 ➕ 檢查 |
| `TOK_IF` 分支 | 行號快取 + 表達式守衛 |
| `TOK_WHILE` 分支 | 行號快取 + 表達式守衛 |

---

### 12. LSP 整合測試修正與 VS Code 設定

**問題：** `test_lsp.py` 中 `LSPClient` 使用 `proc.stdout.read1()` 阻塞讀取，非 thread context 下會卡住，導致測試超時。

**修正：** 將 stdout 讀取改為背景 reader thread + `queue.Queue`，所有 response/notification 讀取透過 queue timeout 完成。新增 `recv_notification(method)` 簡化單一通知接收。

**受影響的測試函式：**
- `test_diagnostics` → 改用 `recv_notification("textDocument/publishDiagnostics")`
- `test_did_save` → 改用 `recv_notification("textDocument/publishDiagnostics")`
- `test_did_close` → 先 consume didOpen diagnostics，再取 didClose diagnostics

**新增檔案：**
- `03/emolang-vscode/package.json` — VS Code 擴充套件設定，註冊 `.emo` 語言
- `03/emolang-vscode/extension.js` — `LanguageClient` 啟動 `emolang_lsp.py`

**安裝路徑：**
```
%USERPROFILE%\.vscode\extensions\emolang-lsp
```

**移除方式：** 刪除上述目錄後重新載入 VS Code。

---

### 13. LSP VS Code 擴充套件路徑修正 (2026.06.11)

**問題：** 擴充套件已安裝至 `%USERPROFILE%\.vscode\extensions\emolang-lsp`，但 VS Code 中 LSP 未啟動（無語法突顯、無大綱）。

**原因：** `extension.js` 使用 `context.asAbsolutePath(path.join("..", "emolang_lsp.py"))`，從安裝目錄往上一層找 `emolang_lsp.py`，但實際檔案位於 OneDrive 的 `03/` 目錄下，路徑不匹配。

**修正：** 將 `extension.js` 中的 LSP 腳本路徑改為絕對路徑：
- `C:/Users/e3545/OneDrive/桌面/ccc114b/系統程式/_sp/03/emolang_lsp.py`

**修改的檔案：**
- `%USERPROFILE%\.vscode\extensions\emolang-lsp\extension.js` — 硬編碼路徑修正

**驗證方式：**
- `python3 test_lsp.py` — 15 項測試全部通過
- VS Code 重新載入後，打開 `.emo` 檔案應有語法突顯與大綱

---

### 14. 移除 VS Code 延伸套件與 LSP 測試 (2026.06.11)

**決定：** 取消 VS Code 上的 LSP 整合，移除延伸套件及相關測試檔案。

**移除的項目：**
| 項目 | 說明 |
|------|------|
| `emolang-vscode/` | VS Code 擴充套件目錄（extension.js, package.json） |
| `test_lsp.py` | LSP 整合測試 |
| `~/.vscode/extensions/emolang-lsp/` | 已安裝的 VS Code 延伸套件 |
| 相關 `__pycache__` | LSP 與測試的編譯快取 |

**保留的項目：**
- `emolang_lsp.py` — LSP 伺服器主程式仍保留，可供其他編輯器或程式使用
- `emolang.py` — GUI/CLI/REPL 主程式不受影響
- `emolang/` — 核心套件（lexer/parser/evaluator）維持原狀
- 大綱面板、語法突顯、程式碼摺疊等 GUI 功能均正常運作

---

### 15. 移除跳至定義 + 錯誤行號修復 + 快捷鍵強化 (2026.06.11)

**移除功能：**
- 移除 `F12` / `Ctrl+G` 跳至定義快捷鍵
- 移除 `_get_def_map()` 與 `_go_to_definition()` 方法

**問題修復：**
1. **空字串 `""` bare expression 未報錯** — 移除 diagnostic parser 中 `AST_STR and expr.name == ""` 的豁免，`""` 現在與其他 bare expression 一樣標記「少了 📢」
2. **快捷鍵重複執行** — `Ctrl+O/N/S` 同時綁定 `code_text` 和 `root` 導致事件冒泡觸發兩次；code_text binding 加入 `or "break"` 阻斷傳播
3. **get_tokens 行號錯亂** — `RuntimeError` 發生在 `\n` 位置時，錯誤恢復的 `pos += 1` 跳過換行但未增 `lexer.line`，導致後續所有 token 行號錯誤，語法突顯無法正確套用。修正為跳過時偵測 `\n` 並同步更新行號/欄位
4. **錯誤標記重現** — `error_tag`（深紅背景 + 底線）在 root cause 修復後安全加回，維持最低優先權不覆蓋語法顏色

**新增功能：**
- `Ctrl+O` — 開啟檔案 (`open_file`)
- `Ctrl+N` — 新建檔案 (`new_file`)
- `Ctrl+S` — 儲存檔案 (`save_file`)

**修改的檔案：**
- `emolang.py`: 移除 `_get_def_map`、`_go_to_definition` 方法及 F12/Ctrl+G 綁定；新增 Ctrl+O/N/S 綁定；所有 code_text 快捷鍵回傳 `"break"`；加回 `error_tag` 設定與套用
- `emolang_lsp.py`: `get_tokens` 錯誤恢復加入 `\n` 行號同步
- `emolang/src/parser.py`: 移除 `AST_STR and expr.name == ""` 豁免

---

### 16. Emoji 鍵盤改版 + 快捷鍵映射功能 (2026.06.11)

**內建鍵盤重新排版：**
- 改為 3 個區塊橫排，每區塊左側有類別標籤：
  - `📦 變數‧流程` — 宣告、輸出/輸入、流程控制、區塊 (15 個)
  - `🛠 函式‧資料` — 函式、結構、指標、資料結構 (15 個)
  - `➕ 運算‧比較` — 算術、比較、邏輯 (11 個)
- 修復 `🛠️`（含 VS16）在 tkinter 按鈕中圖示變形的問題 — 改為 `🛠` 不帶變體選擇器

**新增快捷鍵映射功能：**
- `_emoji_key_map` 字典：字母鍵 → emoji 對應
- `emoji_keys.json`：持久化儲存（自動載入/儲存）
- `_configure_emoji_keys()` 設定視窗：
  - 可滾動列表顯示所有 emoji 與當前按鍵綁定
  - 點選 emoji → 按字母鍵設定快捷鍵
  - 支援清除按鍵、恢復預設
- `toggle_emoji_key_mode()` 切換快捷鍵模式：
  - `⌨️ 模式`（一般模式）→ 按鍵正常輸入
  - `🔣 模式`（紫底）→ 按字母鍵插入對應 emoji
- 工具列按鈕新增中文文字標示（`🔣 鍵盤`、`⌨️ 模式`、`⚙ 設定`）

**問題修復：**
- 設定視窗滾輪無法滾動 — 綁定 `<MouseWheel>` / `<Button-4>` / `<Button-5>` 到 canvas
- VS16 變體選擇器 (`\ufe0f`) 在多處 tkinter widget 中導致圖示渲染異常 — 統一在顯示時移除

**修改的檔案：**
- `emolang.py`: 新增 `EMOJI_KEY_CONFIG_FILE`、`DEFAULT_EMOJI_KEY_MAP`；重新實作 emoji_frame 為 3 區塊橫排；新增 `_load_emoji_key_map()`、`_save_emoji_key_map()`、`toggle_emoji_key_mode()`、`_configure_emoji_keys()`；修改 `_on_code_keypress()` 支援快捷鍵模式；工具列按鈕加入文字標示

---

### 17. 程式碼模組拆分 — emolang.py 重構 (2026.06.11)

**目標：** 將 1237 行的單一 `emolang.py` 按功能拆分為 7 個 mixin 模組 + 1 個 constants 模組，改善可維護性。

**做法：** 使用 Python多重繼承（Mixin pattern），每個 mixin class 定義一組相關方法，`EmoLangGUI` 繼承所有 mixin，保留 `self.method()` 呼叫模式。

**最終檔案結構：**

```
emolang/
├── __init__.py        — 核心函式庫匯出
├── constants.py       — EMOJI_NAMES, SEMANTIC_TAG_MAP, EMOJI_KEY_CONFIG_FILE, DEFAULT_EMOJI_KEY_MAP
├── widgets.py         — ToolTip, GhostText（不變）
├── folding.py         — FoldingMixin（摺疊/展開邏輯）
├── highlighting.py    — HighlightingMixin（語法高亮 + 診斷）
├── outline.py         — OutlineMixin（大綱面板）
├── hover.py           — HoverMixin（滑鼠懸浮提示）
├── refactor.py        — RefactorMixin（重新命名 + 參照搜尋）
├── emoji_panel.py     — EmojiMixin（emoji 工具列 + 快捷鍵設定）
├── suggestions.py     — SuggestionsMixin（幽靈文字 + 自動完成）
└── src/               — 核心直譯器（不變）
```

**`emolang.py` 行數變化：** 1237 → 526 (縮減 57%)

**各模組行數：**

| 檔案 | 行數 |
|------|------|
| `emolang.py` | 526 |
| `emolang/constants.py` | 69 |
| `emolang/folding.py` | 101 |
| `emolang/highlighting.py` | 121 |
| `emolang/outline.py` | 52 |
| `emolang/hover.py` | 71 |
| `emolang/refactor.py` | 101 |
| `emolang/emoji_panel.py` | 159 |
| `emolang/suggestions.py` | 93 |

**修改的檔案：**
- `emolang.py`: 常數移至 `constants.py`；類別改為多重繼承 `class EmoLangGUI(FoldingMixin, HighlightingMixin, OutlineMixin, HoverMixin, RefactorMixin, EmojiMixin, SuggestionsMixin)`；保留 19 個核心方法（init, create_widgets, scroll, file ops, run, undo/redo）；移除 32 個已提取方法
- `emolang/constants.py`: **新增** — 集中管理 EMOJI_NAMES, SEMANTIC_TAG_MAP, EMOJI_KEY_CONFIG_FILE, DEFAULT_EMOJI_KEY_MAP
- `emolang/folding.py`: **新增** — FoldingMixin（`_get_folding_ranges`, `_fold_all`, `_unfold_all`, `_unfold_marker_at_line`, `_on_fold_click`）
- `emolang/highlighting.py`: **新增** — HighlightingMixin（`_apply_semantic_highlighting`, `_update_error_label`, `_show_diagnostics`）
- `emolang/outline.py`: **新增** — OutlineMixin（`_schedule_outline_update`, `_do_update_outline`, `_add_outline_node`, `_on_outline_select`）
- `emolang/hover.py`: **新增** — HoverMixin（`_find_token_at`, `on_mouse_move`, `_show_hover_tooltip`, `_on_mouse_leave`）
- `emolang/refactor.py`: **新增** — RefactorMixin（`_get_all_id_tokens`, `_show_references`, `_rename_symbol`）
- `emolang/emoji_panel.py`: **新增** — EmojiMixin（`toggle_emoji`, `toggle_emoji_key_mode`, `_load_emoji_key_map`, `_save_emoji_key_map`, `_configure_emoji_keys`）
- `emolang/suggestions.py`: **新增** — SuggestionsMixin（`insert_emoji`, `remove_ghost`, `show_ghost`, `update_suggestion`, `on_key_release`, `on_enter`, `on_tab`, `on_up`, `on_down`）

---

### 18. 摺疊後復原凍結問題 — 除錯嘗試 (2026.06.11)

**問題回報：** 摺疊程式碼後按下 `Ctrl+Z`（復原）導致編輯器完全凍結（卡死）。

**除錯過程（4 次迭代，均未解決）：**

| 嘗試 | 做法 | 結果 |
|------|------|------|
| 1 | `_fold_all`/`_unfold_all` 加入 `edit_separator()`；`_safe_undo` 重建摺疊狀態 | 凍結未解決 |
| 2 | `undo=False` 執行摺疊操作；`after_idle` 延遲高亮；`_apply_semantic_highlighting` 提前返回 | 凍結未解決 |
| 3 | 單次 `delete()` + `insert()` 取代逐區塊操作 | 凍結未解決 |
| 4 | 回歸逐區塊方案，無 `edit_separator()`；`_fold_all` 進入時驗證 marker 有效性 | 凍結未完全解決 + backspace 也觸發凍結 |

**最終決策：** 所有修改回退至 GitHub 原始版本（`git checkout --`），問題待重新釐清。

---

### 19. 摺疊復原修復 + 狀態欄清理 (2026.06.11)

**問題：**
1. 摺疊的 `delete`/`insert` 操作污染 Tkinter undo stack，復原時可能撤銷摺疊導致文字與 `_folded_regions` 不一致，程式卡死
2. 摺疊後復原再重做，因 `_folded_regions` 未清空，按摺疊無反應
3. 復原/重做後 `_debug_label` 仍顯示舊的摺疊訊息
4. 開檔時 `_unfold_all()` 無條件顯示「已展開全部區塊」
5. REPL 啟動時 `highlight_ansi('# ...')` 因 lexer 不認得 `#` 而 crash

**修改的檔案：**

- `emolang/folding.py`:
  - `_fold_all` — 先檢查 `_folded_regions` 若非空則呼叫 `_unfold_all()` 展開再重新摺疊；摺疊操作前後用 `config(undo=False/True)` 包裹，防止污染 undo stack；摺疊後呼叫 `_apply_semantic_highlighting()` 刷新語法高亮與狀態欄
  - `_unfold_all` — `undo=False/True` 包裹；加入 `had_folded` 判斷，僅在有實際摺疊區域時才顯示「已展開全部區塊」
  - `_unfold_marker_at_line` — `undo=False/True` 包裹

- `emolang/suggestions.py`:
  - `on_key_release` — 每個操作各自 `try/except` 隔離，單一環節例外不卡死整串事件
  - `update_suggestion` — 加入 `try/except` 保護

- `emolang.py`:
  - `_safe_undo` / `_safe_redo` — 操作後清除 `_debug_label`（`config(text="")`）

- `emolang_lsp.py`:
  - `highlight_ansi` — `tokenize()` 用 `try/except` 保護，失敗時回傳純文字

- `emolang.py` (REPL):
  - `run_repl()` banner 文字從 `#` 改為 `📢`（避免 lexer 錯誤）

