> 本專案由opencode撰寫，參考ccckmit的08-comment_v1目錄
  [網址](https://github.com/ccc114b/cpu2os/tree/master/02-%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F/_books/_code/02-compiler/08-comment_v1)

# p0 編譯器與虛擬機

## 概述

`compiler.c` 是一個精簡的編譯器 + 虛擬機實作，支援整數運算、條件判斷、while 迴圈、函數定義與遞迴呼叫。原始碼經過詞法分析、語法解析產生四元組中間碼，再由虛擬機執行。

---

## 1. while 迴圈處理 — 設計原理

### 語法定義 (EBNF)

```ebnf
while_statement = "while" "(" expression ")" "{" { statement } "}" ;
```

### 中間碼生成策略

while 迴圈使用 **條件跳轉 + 無條件跳轉** 搭配 **Backpatching（回填）** 技術：

```
loop_start:                  ; 記錄 expression 開始前的位置
    condition = expression   ; 計算條件
    JMP_F condition, ?       ; 條件為 false → 跳出（先填 ?）
    body                     ; 迴圈本體
    JMP -, -, loop_start     ; 無條件跳回條件判斷
```

#### 原始碼範例

```c
while (i < 11) {
    sum = sum + i;
    i = i + 1;
}
```

#### 產生的四元組

```
IMM      11         -          t1         ; 載入常數 11
CMP_LT   i          t1         t2         ; i < 11 → t2
JMP_F    t2         -          9          ; t2 為 false 則跳離
ADD      sum        i          t3         ; sum + i → t3
STORE    t3         -          sum
IMM      1          -          t4         ; 載入常數 1
ADD      i          t4         t5         ; i + 1 → t5
STORE    t5         -          i
JMP      -          -          0          ; 跳回指令 0
```

### Backpatching（回填）

兩個跳轉目標在解析當下是未知的：

| 跳轉指令 | 問題 | 解法 |
|----------|------|------|
| `JMP_F` | body 尚未解析，跳轉目標未知 | 先記錄索引 `jmp_idx`，解析完 body 後回填 |
| `JMP` | 要跳回條件判斷處，位置已知 | 在解析 while 前先記錄 `loop_start = quad_count` |

實作流程：

```c
int loop_start = quad_count;        // ① 記錄迴圈條件起始位置
expression(cond);                   // ② 解析條件
int jmp_idx = quad_count;           // ③ 記錄 JMP_F 位置
emit("JMP_F", cond, "-", "?");     // ④ 先填 ?
while (...) statement();            // ⑤ 解析 body
emit("JMP", "-", "-", "");         // ⑥ 發出無條件跳轉
sprintf(quads[quad_count-1].result, "%d", loop_start); // ⑦ JMP 跳回 loop_start
sprintf(quads[jmp_idx].result, "%d", quad_count);       // ⑧ 回填 JMP_F
```

### 虛擬機執行流程

- **JMP_F**：`arg1` 為 0（false）時將 `pc = result - 1`，跳出迴圈
- **JMP**：無條件將 `pc = result - 1`，回到條件判斷處

兩個指令都用 `pc = result - 1`，因為主迴圈每次結束會 `pc++`，-1 才能精確跳到目標。

### while 與 if 的對比

| 特性 | if | while |
|------|----|-------|
| 條件為 false | 跳過 body | 跳出迴圈 |
| 條件為 true | 執行 body 一次 | 重複執行 body |
| 跳轉指令 | 只有 JMP_F | JMP_F + JMP 回跳 |

---

## 2. 函數呼叫機制

### 編譯階段

#### 函數定義

原始碼 `func factorial(n) { ... }` 產生的四元組：

```
FUNC_BEG   factorial  -          -         ; 標記函數起點
FORMAL     n          -          -         ; 宣告形式參數 n
... (函數本體) ...
FUNC_END   factorial  -          -         ; 標記函數終點
```

- `FUNC_BEG` / `FUNC_END` 包裹整個函數定義，VM 遇到 `FUNC_BEG` 時直接跳過
- `FORMAL` 從呼叫者傳入的參數值中取值，建立區域變數

#### 函數呼叫

原始碼 `factorial(5)` 拆解為：

```
PARAM      t8         -          -         ; 將參數值推入 param_stack
CALL       factorial  1          t9        ; 呼叫 factorial(1個參數)，結果存入 t9
```

- `PARAM`：將參數值推入 `param_stack`
- `CALL`：記錄返回地址與目標變數，跳轉到函數入口

返回語句 `return n * factorial(n-1)`：

```
PARAM      t5         -          -         ; 推入 n-1
CALL       factorial  1          t6        ; 遞迴呼叫
MUL        n          t6         t7        ; n * t6
RET_VAL    t7         -          -         ; 回傳 t7
```

### 執行階段：堆疊幀 (Stack Frame)

VM 使用 `Frame stack[]` 實現函數呼叫，`sp` 指向當前框架。

#### Frame 結構

```c
typedef struct {
    char names[100][32];    // 區域變數名稱
    int values[100];        // 區域變數值
    int count;              // 變數數量
    int ret_pc;             // 返回地址
    char ret_var[32];       // 結果存入呼叫者的哪個變數
    int incoming_args[10];  // 傳入的參數值
    int formal_idx;         // 參數處理計數器
} Frame;
```

#### 遞迴流程圖解

以 `factorial(5)` 為例：

```
sp=0  [全域]
sp=1  [factorial, n=5]
sp=2  [factorial, n=4]
sp=3  [factorial, n=3]
sp=4  [factorial, n=2]
sp=5  [factorial, n=1]
sp=6  [factorial, n=0]    → return 1
                            → sp=5, 回傳值寫入 sp=5 的 t6
                            → pc 回到 MUL 指令
```

#### 關鍵指令行為

| 指令 | 行為 |
|------|------|
| `PARAM` | 將值推入全域 `param_stack` |
| `CALL` | `sp++`，建立新 Frame，從 `param_stack` 搬參數，跳轉到函數入口 |
| `FORMAL` | 從 `incoming_args` 取值，在當前 Frame 建立區域變數 |
| `RET_VAL` | 保存回傳值，`sp--`，將值寫入呼叫者 Frame 的目標變數，跳回 `ret_pc` |
| `FUNC_BEG` | VM 直接跳過（函數不自動執行） |
| `FUNC_END` | 函數結尾，自然結束 |

### 支援遞迴的關鍵

每次 `CALL` 都會 `sp++` 建立全新的 Frame：

- 每個 Frame 有獨立的 `names[]` / `values[]`，變數完全隔離
- `ret_pc` 確保回傳後能精確回到正確的指令
- `ret_var` 確保回傳值能寫入正確的接收變數

這就是 `factorial(5)` 可以正確算出 `120` 的原因。

---

## 程式列表

| 檔案 | 說明 |
|------|------|
| `compiler.c` | 編譯器 + 虛擬機實作 |
| `call.md` | 函數呼叫機制詳細說明 |
| `p0/` | 測試程式 (.p0) 與執行結果 (.md) |
| `p0/fact.p0` | 階乘遞迴範例 |
| `p0/prime.p0` | 質數判斷遞迴範例 |
| `p0/while.p0` | while 迴圈範例 |
| `p0/if.p0` | if 條件判斷範例 |
| `p0/add.p0` | 加法運算範例 |
