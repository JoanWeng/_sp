# EmoLang — Emoji 程式語言直譯器

EmoLang 是一款以 **Emoji 作為關鍵字**的程式語言直譯器，採用**樹狀走訪直譯 (Tree-Walk Interpretation)** 模型，且為 **零相依 (Zero-Dependency)** 架構——完全不依賴 C 標準庫 (`<stdio.h>`, `<stdlib.h>` 等)，直接透過 POSIX 系統呼叫與作業系統溝通。

---

## 目錄

1. [專案架構總覽](#1-專案架構總覽)
2. [執行流程（一條龍解析）](#2-執行流程一條龍解析)
3. [模組逐層解析](#3-模組逐層解析)
   - [3.1 標頭檔層 (include/)](#31-標頭檔層-include)
   - [3.2 底層引擎 (io.c / utils.c)](#32-底層引擎-ioc-utilsc)
   - [3.3 詞法分析器 (lexer.c)](#33-詞法分析器-lexerc)
   - [3.4 語法分析器 (parser.c)](#34-語法分析器-parserc)
   - [3.5 AST 記憶體池 (ast.c)](#35-ast-記憶體池-astc)
   - [3.6 虛擬記憶體與符號表 (memory.c)](#36-虛擬記憶體與符號表-memoryc)
   - [3.7 求值引擎 (eval.c)](#37-求值引擎-evalc)
   - [3.8 主程式入口 (main.c)](#38-主程式入口-mainc)
4. [EmoLang 語法完整參考](#4-emolang-語法完整參考)
5. [核心設計理念](#5-核心設計理念)
6. [編譯與執行](#6-編譯與執行)

---

## 1. 專案架構總覽

```
02/
├── emolang                  # 編譯好的可執行檔 (ELF 64-bit)
├── README.md                # 原有說明
├── newREADME.md             # 本文件
│
├── include/                 # 標頭檔目錄
│   ├── emolang.h            # 核心定義：Token、AST、Value、全域變數宣告
│   ├── io.h                 # I/O 與系統呼叫介面宣告
│   └── utils.h              # 自製字串/數學函式 + 巨集重映射
│
├── src/                     # 原始碼目錄 (7 個模組)
│   ├── main.c               # 主程式進入點：讀檔 → 解析 → 執行
│   ├── lexer.c              # 詞法分析器 (Lexer)：字元 → Token
│   ├── parser.c             # 語法分析器 (Parser)：Token → AST
│   ├── ast.c                # AST 節點靜態記憶體池
│   ├── eval.c               # 求值引擎 (Evaluator)：走訪 AST 並執行
│   ├── memory.c             # 虛擬記憶體、符號表、call stack
│   ├── io.c                 # POSIX 系統呼叫包裝 (無 libc)
│   └── utils.c              # 徒手實作的字串/型別轉換工具
│
├── emoTests/                # EmoLang 腳本範例
│   ├── test.emo             # 存錢買遊戲機範例 (while, if/else)
│   ├── test2.emo            # for 迴圈、結構體、多重指標
│   ├── test3.emo            # 陣列配置、輸入、結構體整合
│   ├── test4.emo            # 動態型別、else if 鏈
│   ├── funcTest.emo         # 綜合測試：函數、迴圈、結構、指標、輸入
│   ├── listDictTest.emo     # 動態列表 (List) 與字典 (Dict)
│   └── logicTest.emo        # 邏輯運算 (AND / OR / NOT)
│
└── docs/
    ├── 使用指南.md           # Emoji 語法完整對照表
    └── 程式碼解析.md         # 原始碼逐行解析文件
```

---

## 2. 執行流程

EmoLang 的直譯器採用經典的三階段 pipeline：

```
原始碼 (.emo)
    │
    ▼
┌─────────────┐
│   Lexer     │  ← 詞法分析 (src/lexer.c)
│  (切詞器)   │     逐字元掃描，輸出 Token 串流
└──────┬──────┘
       │ Token 串流
       ▼
┌─────────────┐
│   Parser    │  ← 語法分析 (src/parser.c)
│  (建樹器)   │     遞迴下降解析，輸出 AST
└──────┬──────┘
       │ AST (抽象語法樹)
       ▼
┌─────────────┐
│  Evaluator  │  ← 求值執行 (src/eval.c)
│  (執行器)   │     遞迴走訪 AST 節點，操作虛擬記憶體
└─────────────┘
       │
       ▼
   執行結果 (stdout / 記憶體變更)
```

**main.c 中的實際呼叫流程：**

```
main()
 ├─ my_open()                // 透過系統呼叫 open() 讀取 .emo 檔
 ├─ my_lseek()               // 取得檔案大小
 ├─ my_read()                // 將原始碼讀入 1MB 緩衝區
 ├─ my_close()
 │
 ├─ advance_token()          // 初始化，讀入第一個 Token
 │
 ├─ while (not EOF)          // 主解析迴圈
 │   └─ parse_statement()    // 逐一解析語句，串成 AST 鏈表
 │
 └─ execute(program)         // 執行整棵 AST
```

---

## 3. 模組逐層解析

### 3.1 標頭檔層 (include/)

#### `emolang.h` — 核心藍圖

整個專案的神經中樞，定義了所有資料結構與全域變數的外部連結。

**Token 類型 (`TokenType`) — 41 種**

| 類別 | Token | 對應 Emoji |
|------|-------|-----------|
| 變數宣告 | `TOK_LET` | `📦`, `🔢`, `🎈`, `📝`, `🚦` |
| 賦值 | `TOK_ASSIGN` | `🟰` |
| 控制流 | `TOK_IF`, `TOK_ELSE`, `TOK_WHILE`, `TOK_FOR` | `🤔`, `🤷`, `🔁`, `🎡` |
| 區塊 | `TOK_LBRACE`, `TOK_RBRACE` | `👇`, `👆` |
| 輸出/輸入 | `TOK_PRINT`, `TOK_INPUT` | `📢`, `📥` |
| 算術 | `TOK_PLUS`, `TOK_MINUS`, `TOK_MUL`, `TOK_DIV`, `TOK_MOD` | `➕`, `➖`, `✖️`, `➗`, `✂️` |
| 比較 | `TOK_EQ`, `TOK_GT`, `TOK_LT` | `🤝`, `📈`, `📉` |
| 邏輯 | `TOK_AND`, `TOK_OR`, `TOK_NOT` | `🔗`, `🔀`, `🙅` |
| 結構 | `TOK_STRUCT`, `TOK_NEW`, `TOK_DOT` | `🏗️`, `🆕`, `➡️` |
| 指標 | `TOK_REF`, `TOK_DEREF` | `📍`, `🎯` |
| 陣列 | `TOK_ARRAY`, `TOK_INDEX` | `📚`, `📌` |
| 函數 | `TOK_FUNC`, `TOK_RETURN` | `🛠️`, `🔙` |
| 列表/字典 | `TOK_LIST`, `TOK_DICT`, `TOK_APPEND`, `TOK_LEN` | `📋`, `📖`, `🛒`, `📏` |
| 基礎值 | `TOK_NUM`, `TOK_FLOAT_NUM`, `TOK_TRUE`, `TOK_FALSE`, `TOK_STR`, `TOK_ID` | `🟢`, `🔴` |
| 符號 | `TOK_LPAREN`, `TOK_RPAREN`, `TOK_COMMA`, `TOK_SEP` | `(`, `)`, `,`, `🚧` |

**Value 結構 — 動態型別核心**

```c
typedef struct { int type; int i; double f; char s[256]; } Value;
```

| type | 代表型別 | 儲存欄位 |
|:----:|:--------|:---------|
| 0 | 整數 / 布林 (True=1, False=0) | `.i` |
| 1 | 浮點數 (float) | `.f` |
| 2 | 字串 (string) | `.s[256]` |
| 3 | 動態列表 (list) — 儲存 list_pool 的 ID | `.i` |
| 4 | 動態字典 (dict) — 儲存 dict_pool 的 ID | `.i` |

**AST 節點 (`ASTNode`) — 語法樹的基本單元**

```c
typedef struct ASTNode {
    ASTType type;          // 節點類型 (如 AST_BINOP, AST_LET, AST_IF...)
    TokenType op;          // 二元運算子類型 (如 TOK_PLUS, TOK_EQ...)
    char name[256];        // 變數/函數/結構名稱
    int value;             // 整數常數值
    double f_val;          // 浮點數常數值
    struct ASTNode *left, *right;         // 二元運算左右運算元
    struct ASTNode *true_branch, *false_branch; // 條件分支
    struct ASTNode *cond, *step;          // for 迴圈條件與步進
    struct ASTNode *body, *next;          // 區塊本體與鏈表 next
} ASTNode;
```

**支援的 AST 節點類型 (共 28 種)**

`AST_LET`, `AST_ASSIGN`, `AST_IF`, `AST_WHILE`, `AST_FOR`, `AST_PRINT`,
`AST_BLOCK`, `AST_BINOP`, `AST_NUM`, `AST_STR`, `AST_VAR`,
`AST_STRUCT_DEF`, `AST_NEW`, `AST_DOT`, `AST_REF`, `AST_DEREF`,
`AST_ARRAY_ALLOC`, `AST_INDEX`, `AST_INPUT`, `AST_FLOAT`, `AST_TRUE`, `AST_FALSE`,
`AST_FUNC_DEF`, `AST_FUNC_CALL`, `AST_RETURN`, `AST_NOT`,
`AST_NEW_LIST`, `AST_NEW_DICT`, `AST_APPEND`, `AST_LEN`

**記憶體與狀態結構**

```c
typedef struct { char name[256]; char fields[20][256]; int field_count; } StructDef;
// 結構定義表：名稱 + 最多 20 個欄位

typedef struct { char name[256]; ASTNode *params; ASTNode *body; } FuncDef;
// 函數定義表：名稱 + 參數串列 + 函數主體 AST

typedef struct { char name[256]; int addr; } Symbol;
// 符號表項目：變數名稱 → 虛擬記憶體位址

typedef struct { Value items[100]; int count; } ListObj;
// 動態列表：最多 100 個元素

typedef struct { char keys[100][256]; Value values[100]; int count; } DictObj;
// 動態字典：最多 100 個鍵值對
```

**全域變數宣告**

```c
extern char *src_code;                     // 原始碼緩衝區指標
extern int src_pos;                        // 目前掃描位置
extern Token current_token;                // 當前 Token

extern Value memory[MEM_SIZE];             // 虛擬記憶體 (MEM_SIZE=10000)
extern int heap_ptr;                       // 堆積指標

extern StructDef struct_table[50];         // 結構定義表
extern int struct_count;
extern FuncDef func_table[50];            // 函數定義表
extern int func_count;

extern ListObj list_pool[100];            // 列表物件池
extern int list_count;
extern DictObj dict_pool[100];            // 字典物件池
extern int dict_count;

extern Symbol sym_stack[20][100];          // 符號表呼叫堆疊
extern int sym_count[20];
extern int call_depth;                     // 當前呼叫深度 (0 = 全域)

extern Value ret_val;                      // 函數返回值
extern int is_returning;                   // 返回標誌
```

---

#### `io.h` — I/O 與系統呼叫介面

宣告所有與作業系統溝通的函式，包括：

- **基本 I/O**: `my_print_str`, `my_print_int`, `my_print_float`, `my_print_newline`, `my_read_str`
- **POSIX 系統呼叫包裝**: `my_open`, `my_lseek`, `my_read`, `my_close`, `my_exit`
- **錯誤處理**: `my_error` — 統一的崩潰處理器

---

#### `utils.h` — 工具函式 + 巨集魔法

宣告自製字串函式 (`my_strlen`, `my_strcmp`, `my_strcpy` 等) 與型別轉換 (`my_atoi`, `my_atof`, `my_itoa`, `my_ftoa`)。

**巨集重映射 (Macro Remapping)** — 關鍵設計：

```c
#define strlen my_strlen
#define strcmp my_strcmp
#define strcpy my_strcpy
// ... 等 11 個巨集
```

這讓原始碼中可以直接寫 `strlen()` 等標準名稱，編譯器會自動導向自訂實作。

---

### 3.2 底層引擎 (io.c / utils.c)

#### `io.c` — 直接與 OS 對話

完全不使用 `<stdio.h>` / `<stdlib.h>`，而是**直接宣告 Linux 系統呼叫**：

```c
extern long write(int fd, const void *buf, unsigned long count);
extern long read(int fd, void *buf, unsigned long count);
extern int open(const char *pathname, int flags);
extern long lseek(int fd, long offset, int whence);
extern int close(int fd);
extern void _exit(int status);
```

- **`my_print_int`**: 透過 `取餘數 → 反轉字串` 演算法將整數轉為 ASCII 字串輸出
- **`my_print_float`**: 分拆整數與小數部分，小數固定輸出 4 位
- **`my_read_str`**: 從 stdin 逐字元讀取，遇 `\n` 或空格結束
- **`my_error`**: 印出錯誤訊息後呼叫 `_exit(1)` 終止程式

#### `utils.c` — 徒手實作字串函式庫

完全用裸指標運算實作：

| 函式 | 演算法 |
|:-----|:-------|
| `my_strlen` | 逐字元計數直到 `\0` |
| `my_strcmp` | 逐字元比對，回傳 ASCII 差值 |
| `my_strncpy` | 限長複製 + `\0` 補齊 |
| `my_atoi` | `res = res * 10 + (c - '0')` |
| `my_atof` | 整數部分 + 小數部分 (`fraction *= 0.1`) |
| `my_itoa` | 取餘數收集位數 → 反轉陣列 |
| `my_ftoa` | 拆整數 + 小數，分別轉字串 |

---

### 3.3 詞法分析器 (lexer.c)

**功能**：將原始碼字元串流轉換為 Token 串流。

**關鍵資料結構**：

```c
// 41 個 Emoji 關鍵字 → Token 對應表
const char *emoji_keywords[] = {
    "📦", "🔢", "🎈", "📝", "🚦", "🟰", "🤔", "🤷", "🔁", "👇",
    "👆", "📢", "➕", "➖", "✖️", "➗", "✂️", "🤝", "📈", "📉",
    "🎡", "🚧", "🏗️", "🆕", "➡️", "📍", "🎯", "📚", "📌", "📥",
    "🟢", "🔴", "🛠️", "🔙", "🔗", "🔀", "🙅",
    "📋", "📖", "🛒", "📏"
};
```

**`advance_token()` 的解析順序**：

1. **跳過空白** (`isspace`)
2. **檢查 EOF**
3. **標點符號**: `(`, `)`, `,`
4. **字串**: 雙引號 `"..."` 包圍的內容
5. **數字**: 含 `.` 判斷為浮點數，否則為整數
6. **Emoji 關鍵字**: 呼叫 `match_keyword()` 進行 UTF-8 位元組比對
7. **普通識別符 (ID)**: 非 Emoji、非符號的連續字元

**`match_keyword()` 的運作原理**：
- 逐一比對 `emoji_keywords[i]` 的字串長度
- 使用 `strncmp` 比對原始碼目前位置
- Emoji 在 UTF-8 編碼中佔 3~4 個 bytes，此處用字串比對處理

---

### 3.4 語法分析器 (parser.c)

**功能**：將 Token 串流轉換為抽象語法樹 (AST)。

採用**遞迴下降解析 (Recursive Descent Parsing)**，按照運算子優先級由低到高分層：

```
parse_statement()          ← 最高層：語句解析
  ├── TOK_FUNC    → AST_FUNC_DEF
  ├── TOK_RETURN  → AST_RETURN
  ├── TOK_LET     → AST_LET
  ├── TOK_PRINT   → AST_PRINT
  ├── TOK_IF      → AST_IF (含 else/else if)
  ├── TOK_WHILE   → AST_WHILE
  ├── TOK_FOR     → AST_FOR (init; cond; step)
  ├── TOK_STRUCT  → AST_STRUCT_DEF
  └── 表達式      → 可能接 ASSIGN / APPEND

parse_expression()         ← 邏輯 OR (🔀) — 優先級最低
  └── parse_logical_and()  ← 邏輯 AND (🔗)
       └── parse_comparison()  ← 比較 (🤝, 📈, 📉)
            └── parse_addition()    ← 加減 (➕, ➖)
                 └── parse_factor()  ← 乘除餘 (✖️, ➗, ✂️)
                      └── parse_prefix()   ← 前綴 (🙅, 📏, 📥, 📍, 🎯, 🆕)
                           └── parse_postfix()  ← 後綴 (➡️, 📌)
                                └── parse_primary()  ← 基礎值 (數字, 字串, 變數, 括號)
```

**優先級層級表**：

| 層級 | 函式 | 運算子 | 結合性 |
|:----:|:-----|:-------|:------:|
| 1 (最高) | `parse_primary` | `()` `數字` `字串` `變數` `函數呼叫` | — |
| 2 | `parse_postfix` | `➡️` (成員存取), `📌` (索引) | 左 |
| 3 | `parse_prefix` | `🙅` `📏` `📥` `📍` `🎯` `🆕` | 右 |
| 4 | `parse_factor` | `✖️` `➗` `✂️` | 左 |
| 5 | `parse_addition` | `➕` `➖` | 左 |
| 6 | `parse_comparison` | `🤝` `📈` `📉` | 左 |
| 7 | `parse_logical_and` | `🔗` | 左 |
| 8 (最低) | `parse_expression` | `🔀` | 左 |

**特殊語法解析細節**：

- **函數呼叫判斷**: 變數 (`TOK_ID`) 後接 `TOK_LPAREN` 時判定為 `AST_FUNC_CALL`
- **區塊解析 (`parse_block`)**: `👇` ... `👆` 之間的所有語句串成鏈表
- **賦值與追加**: 表達式後接 `🟰` → `AST_ASSIGN`；接 `🛒` → `AST_APPEND`
- **Else If 鏈**: `🤷` 後若接 `🤔`，遞迴呼叫 `parse_statement()`

---

### 3.5 AST 記憶體池 (ast.c)

**功能**：提供靜態預先分配的 AST 節點記憶體池。

```c
#define MAX_AST_NODES 50000
ASTNode ast_pool[MAX_AST_NODES];
int ast_node_count = 0;
```

**`create_node(ASTType type)`**：
- 從 `ast_pool` 中取出第 `ast_node_count++` 個節點
- 手動 memset 為 0（指標運算，不使用 `memset`）
- 設定 `type` 後回傳

這種**區域分配器 (Arena Allocator)** 模式效能極高——無需 malloc/free，無記憶體碎片，但節點用完後不會釋放。

---

### 3.6 虛擬記憶體與符號表 (memory.c)

**功能**：管理 EmoLang 虛擬機的所有執行期狀態。

#### 全域變數實體化

| 變數 | 容量 | 用途 |
|:-----|:----|:-----|
| `memory[10000]` | 10000 個 Value | 虛擬記憶體堆積 (heap) |
| `struct_table[50]` | 50 個結構定義 | 自訂結構型別 |
| `func_table[50]` | 50 個函數定義 | 使用者自訂函數 |
| `sym_stack[20][100]` | 20 層 × 100 符號 | 符號表呼叫堆疊 |
| `list_pool[100]` | 100 個列表 | 動態列表儲存池 |
| `dict_pool[100]` | 100 個字典 | 動態字典儲存池 |

#### 作用域 (Scope) 實作

使用 `sym_stack[20][100]` 搭配 `call_depth` 實現**巢狀詞法作用域**：

```
call_depth = 0  (全域層)
  ├── sym_stack[0][0] = { "x", addr=1 }
  ├── sym_stack[0][1] = { "y", addr=2 }
  │
  └── 呼叫函數 foo():
       call_depth = 1
         ├── sym_stack[1][0] = { "param1", addr=10 }
         ├── sym_stack[1][1] = { "local_a", addr=11 }
         │
         └── 呼叫函數 bar():
              call_depth = 2
                └── ...
```

**`get_sym_addr()` 的查找順序**：
1. 先搜尋當前 `call_depth` 層
2. 若 `call_depth > 0` 且找不到，往全域層 (depth=0) 搜尋
3. 仍找不到則報錯

#### 字典操作

- **`dict_set`**: 若鍵已存在則覆蓋，否則新增
- **`dict_get`**: 線性搜尋，找不到則報錯

#### `get_lvalue()` — 賦值左值位址計算

支援四種賦值目標的位址取得：

| 節點類型 | 計算方式 |
|:---------|:---------|
| `AST_VAR` | `get_sym_addr(name)` |
| `AST_DEREF` | `eval(node->left).i`（指標解參照） |
| `AST_INDEX` | `base_addr + index`（陣列索引）；List/Dict 則分派至各自的 pool |
| `AST_DOT` | `struct_addr + 1 + field_offset` |

---

### 3.7 求值引擎 (eval.c)

**功能**：遞迴走訪 AST 並執行語意，是直譯器的大腦。

#### `is_truthy(Value v)` — 布林真值判斷

| 型別 | 真值條件 |
|:----|:---------|
| type 0 (整數) | `i != 0` |
| type 1 (浮點數) | `f != 0.0` |
| type 2 (字串) | `strlen(s) > 0` |
| type 3/4 (列表/字典) | `0` (空即為假) |

#### `assign_value(ASTNode *node, Value val)` — 統一賦值引擎

處理四種賦值情境：

1. **`AST_VAR`**: 直接寫入 `memory[get_sym_addr(name)]`
2. **`AST_DEREF`**: 解參照後寫入 `memory[eval(left).i]`
3. **`AST_DOT`**: 計算結構體成員位址後寫入
4. **`AST_INDEX`**: 依據 base 型別分派：
   - `type==3` (List): 寫入 `list_pool[id].items[idx]`
   - `type==4` (Dict): 呼叫 `dict_set(id, key, val)`
   - 其他 (陣列): 寫入 `memory[base + idx]`

#### `eval(ASTNode *node)` — 表達式求值器 (核心遞迴)

處理 20+ 種 AST 節點類型：

**短路求值 (Short-circuit Evaluation)**：
- `TOK_AND`: 左側為 false → 直接回傳，不計算右側
- `TOK_OR`: 左側為 true → 直接回傳，不計算右側

**字串串接** (`TOK_PLUS` 且任一 operant 為 type 2)：
- 自動將數字/浮點數轉為字串後拼接

**浮點數提升**：任一 operant 為浮點數時，整數自動提升為 double 計算

**函數呼叫** (`AST_FUNC_CALL`) 的執行流程：
1. 在 `func_table` 中尋找函數定義
2. 計算所有參數表達式的值
3. `call_depth++` 建立新作用域層
4. 將參數值依序分配記憶體並註冊到符號表
5. 執行函數主體 `execute(fd->body)`
6. 檢查 `is_returning` 標誌取得回傳值
7. `call_depth--` 回到呼叫者作用域

#### `print_value(Value v)` — 格式化輸出

| Value type | 輸出格式 | 範例 |
|:-----------|:---------|:-----|
| 3 (List) | `[item1, item2, ...]` | `[紅色藥水, 鐵劍, 地圖]` |
| 4 (Dict) | `{"key": value, ...}` | `{"名字": "史萊姆", "血量": 150}` |
| 2 (Str) | 裸字串 | `Hello World` |
| 1 (Float) | 小數 | `3.1415` |
| 0 (Int/Bool) | 整數 | `42` 或 `1` |

#### `execute(ASTNode *stmt)` — 語句執行控制器

依序走訪鏈表中的每個語句節點：

| AST 類型 | 行為 |
|:---------|:-----|
| `AST_RETURN` | 求值 `left` 設為 `ret_val`，設 `is_returning=1` |
| `AST_FUNC_DEF` | 將名稱/參數/主體註冊到 `func_table` |
| `AST_LET` | 配置記憶體 + 選擇性初始化 (含宣告變數) |
| `AST_ASSIGN` | 呼叫 `assign_value()` |
| `AST_APPEND` | 將值推入 List 的 `items[]` 尾端 |
| `AST_STRUCT_DEF` | 解析結構欄位名稱至 `struct_table` |
| `AST_PRINT` | 呼叫 `print_value(eval(left))` |
| `AST_IF` | 條件為真執行 true_branch，否則執行 false_branch |
| `AST_WHILE` | 反覆檢查條件並執行 true_branch |
| `AST_FOR` | 執行 init → while(cond) { body; step; } |

---

### 3.8 主程式入口 (main.c)

**靜態緩衝區**：
```c
char src_buffer[1024 * 1024];  // 1MB 的靜態陣列
```
在編譯期直接分配，無需 `malloc`。

**`main()` 執行步驟**：

```
1. 參數檢查
   └─ argc < 2 → 印出用法提示，return 1

2. OS 檔案讀取
   ├─ my_open(argv[1])           → 取得 fd
   ├─ my_lseek(fd, 0, SEEK_END)  → 取得檔案大小
   ├─ my_lseek(fd, 0, SEEK_SET)  → 回到檔頭
   ├─ my_read(fd, buffer, size)  → 讀入原始碼
   ├─ buffer[size] = '\0'        → 字串終止
   └─ my_close(fd)

3. 詞法分析初始化
   └─ advance_token()            → 讀入第一個 Token

4. 語法解析 (while 迴圈直到 TOK_EOF)
   ├─ parse_statement()          → 每次解析一條語句
   └─ tail->next = stmt          → 串成單向鏈表

5. 執行
   └─ execute(program)           → 啟動直譯器！
```

---

## 4. EmoLang 語法完整參考

### 變數宣告與賦值

| 語法 | 說明 |
|:-----|:-----|
| `📦 名稱 🟰 值` | 通用變數宣告 |
| `🔢 名稱 🟰 整數` | 強調整數變數 |
| `🎈 名稱 🟰 小數` | 強調浮點數變數 |
| `📝 名稱 🟰 "字串"` | 強調字串變數 |
| `🚦 名稱 🟰 🟢/🔴` | 強調布林變數 |
| `名稱 🟰 新值` | 重新賦值 |

### 資料型別

| 型別 | 寫法 |
|:-----|:-----|
| 整數 | `10`, `-3`, `0` |
| 浮點數 | `3.14`, `-0.5` |
| 字串 | `"Hello"`, `"中文"` |
| 布林 | `🟢` (True), `🔴` (False) |
| 陣列 | `🆕 📚 大小` |
| 列表 | `🆕 📋` |
| 字典 | `🆕 📖` |

### 運算子 (依優先級排列)

| 優先級 | 運算子 | 說明 | 範例 |
|:------:|:------|:-----|:-----|
| 1 | `()` | 括號 | `(1 ➕ 2) ✖️ 3` |
| 2 | `➡️` | 結構成員存取 | `物件 ➡️ 欄位` |
| 2 | `📌` | 索引/鍵存取 | `列表 📌 0`, `字典 📌 "鍵"` |
| 3 | `🙅` | 邏輯 NOT | `🙅 條件` |
| 3 | `📏` | 取長度 | `📏 字串/列表/字典` |
| 3 | `📥` | 使用者輸入 | `📦 x 🟰 📥` |
| 3 | `📍` | 取址 (&) | `📍 變數` |
| 3 | `🎯` | 解參照 (*) | `🎯 指標` |
| 3 | `🆕` | 新建 | `🆕 結構`, `🆕 📋` |
| 4 | `✖️` `➗` `✂️` | 乘、除、取餘 | `a ✖️ b` |
| 5 | `➕` `➖` | 加、減 / 字串串接 | `a ➕ b` |
| 6 | `🤝` `📈` `📉` | 等於、大於、小於 | `a 🤝 b` |
| 7 | `🔗` | 邏輯 AND | `條件1 🔗 條件2` |
| 8 | `🔀` | 邏輯 OR | `條件1 🔀 條件2` |

### 控制流

```
🤔 條件 👇
    // true 分支
👆 🤷 🤔 條件2 👇
    // else if 分支
👆 🤷 👇
    // else 分支
👆

🔁 條件 👇
    // 迴圈主體
👆

🎡 init 🚧 條件 🚧 步進 👇
    // for 迴圈主體
👆
```

### 函數

```
🛠️ 函數名稱(參數1, 參數2) 👇
    📦 結果 🟰 ...
    🔙 結果
👆

📦 回傳值 🟰 函數名稱(引數1, 引數2)
```

### 結構體

```
🏗️ 結構名稱 👇
    📦 欄位1
    📦 欄位2
👆

📦 實例 🟰 🆕 結構名稱
實例 ➡️ 欄位1 🟰 值
```

### 列表與字典

```
// 列表
📦 列表 🟰 🆕 📋          // 建立空列表
列表 🛒 "元素"              // 追加元素
列表 📌 0                  // 索引存取
📏 列表                    // 取得長度

// 字典
📦 字典 🟰 🆕 📖          // 建立空字典
字典 📌 "鍵" 🟰 "值"       // 設定鍵值
字典 📌 "鍵"               // 讀取值
📏 字典                    // 取得長度
```

### 指標

```
📍 變數       → 取得變數的虛擬記憶體位址
🎯 指標       → 解參照，存取指標指向的記憶體內容
🎯 指標 ➡️ 欄位  → 透過指標存取結構成員
```

### I/O

```
📢 表達式     → 印出值 (支援所有型別)
📦 x 🟰 📥   → 從終端機讀取輸入 (自動判斷型別)
```

---

## 5. 核心設計理念

### 5.1 零相依 (Zero-Dependency)

不依賴任何 C 標準庫函式。所有 `printf`/`scanf`/`strlen`/`atoi` 等均以**POSIX 系統呼叫** (`write`, `read`, `open`, `_exit`) 搭配手刻演算法重新實作。這使得 EmoLang 具備極高的底層移植性。

### 5.2 區域分配器 (Arena Allocator)

- **AST 節點池**: `ast_pool[50000]` — 高達 50,000 個節點的靜態陣列
- **虛擬記憶體**: `memory[10000]` — 10,000 格的線性記憶體
- 無 `malloc`/`free`，無垃圾回收，無記憶體碎片

### 5.3 遞迴下降解析 (Recursive Descent Parsing)

9 層優先級嵌套，每層一個獨立函式，程式碼結構與語法規則直接對應，易於維護與擴展。

### 5.4 樹狀走訪直譯 (Tree-Walk Interpretation)

無 Bytecode 編譯階段，語法分析完成後立即以遞迴方式走訪 AST 並執行。實作簡單直觀，但大型程式的重複走訪成本較高。

### 5.5 動態弱型別 (Dynamic Weakly Typed)

採用 `Value` 結構封裝 5 種型別，執行期動態決議。支援多型運算（如 `"Hello" ➕ 42` 自動將數字轉字串串接）。

### 5.6 巨集重映射 (Macro Remapping)

```c
#define strlen my_strlen
```
利用 C 前置處理器將標準庫名稱重新導向至自訂實作，使程式碼可讀性與零相依需求兩者兼顧。

---

## 6. 編譯與執行

### 編譯方式

```bash
gcc src/*.c -I include -o emolang
```

### 執行方式

```bash
./emolang emoTests/test.emo       # 執行測試腳本
./emolang emoTests/funcTest.emo   # 函數與綜合測試
./emolang 你的腳本.emo            # 執行自訂腳本
```

### 現有測試腳本一覽

| 檔案 | 測試重點 |
|:-----|:---------|
| `test.emo` | While 迴圈、If/Else 條件判斷 |
| `test2.emo` | For 迴圈、取餘數、結構體、指標 |
| `test3.emo` | 動態陣列配置、使用者輸入 |
| `test4.emo` | 動態型別 (int/float/str/bool)、Else If 鏈、字串串接 |
| `funcTest.emo` | 綜合測試：函數定義與呼叫、巢狀迴圈、結構體、指標、輸入 |
| `listDictTest.emo` | 動態列表 (List) 與字典 (Dict) 操作 |
| `logicTest.emo` | 邏輯運算 AND/OR/NOT、短路求值、複雜條件 |

---

> EmoLang 是系統程式課程的專案，展示了如何從零開始構建一個可運作的程式語言直譯器，涵蓋詞法分析、語法分析、AST 建構與樹狀走訪求值的完整流程。
