## p0 compiler 函數呼叫機制

### 1. 總覽

p0 的函數呼叫機制分為**編譯階段**與**執行階段**。編譯器將高階的函數呼叫與定義拆解為線性的四元組（quadruples），而虛擬機（VM）透過**堆疊幀（Stack Frame）**實作變數隔離與遞迴。

### 2. 編譯階段：四元組生成

#### 2.1 函數定義

原始碼：

```c
func factorial(n) {
    if (n == 0) {
        return 1;
    }
    return n * factorial(n - 1);
}
```

產生的四元組：

```
FUNC_BEG   factorial  -          -         ; 標記函數起點
FORMAL     n          -          -         ; 宣告形式參數 n
... (函數本體) ...
FUNC_END   factorial  -          -         ; 標記函數終點
```

- `FUNC_BEG` / `FUNC_END` 包裹整個函數定義，VM 在掃到 `FUNC_BEG` 時會直接跳過（函數不自動執行）
- `FORMAL` 從呼叫者傳入的參數值中取值，建立區域變數

#### 2.2 函數呼叫

原始碼 `factorial(5)` 被拆解為：

```
PARAM      t8         -          -         ; 將參數值推入參數暫存區
CALL       factorial  1          t9        ; 呼叫 factorial(1個參數)，結果存入 t9
```

- `PARAM`：計算參數表達式後，將值放入 `param_stack`
- `CALL`：記錄返回地址與目標變數，跳轉到函數入口

返回語句 `return n * factorial(n - 1)` 則產生：

```
PARAM      t5         -          -         ; 推入 n-1
CALL       factorial  1          t6        ; 遞迴呼叫，結果進 t6
MUL        n          t6         t7        ; n * t6
RET_VAL    t7         -          -         ; 回傳 t7
```

- `RET_VAL`：將值保留，結束當前堆疊幀，返回呼叫者

### 3. 執行階段：堆疊幀機制

VM 使用 `Frame stack[]` 實現函數呼叫，`sp` 指向當前框架。

#### 3.1 Frame 結構

```c
typedef struct {
    char names[100][32];   // 區域變數名稱
    int values[100];       // 區域變數值
    int count;             // 變數數量
    int ret_pc;            // 返回地址
    char ret_var[32];      // 結果要存入呼叫者的哪個變數
    int incoming_args[10]; // 傳入的參數值
    int formal_idx;        // 參數處理計數器
} Frame;
```

#### 3.2 呼叫流程圖解

以 `factorial(5)` 為例：

```
sp=0  [全域]                   factorial(5) 呼叫時：
                                1. sp++ → sp=1
                                2. 新 Frame.ret_pc = CALL 下一行
                                3. 新 Frame.ret_var = "t9"
                                4. incoming_args = [5]
                                5. pc 跳到 FUNC_BEG 後第一行

sp=1  [factorial, n=5]        遇到 n* factorial(n-1) 時再遞迴：
                                1. sp++ → sp=2
                                2. 新 Frame.ret_pc = MUL 那行
                                3. incoming_args = [4]
                                4. pc 跳到函數入口

sp=2  [factorial, n=4]        以此類推...
sp=3  [factorial, n=3]
sp=4  [factorial, n=2]
sp=5  [factorial, n=1]

sp=6  [factorial, n=0]        遇到 return 1 時：
                                1. ret_val = 1
                                2. sp-- → sp=5
                                3. 將 1 存入 sp=5 的 t6
                                4. pc = sp=5 的 ret_pc (MUL 指令)
```

每一層都有獨立的 `n` 值，不會互相干擾。

#### 3.3 關鍵指令行為

| 指令 | 行為 |
|------|------|
| `PARAM` | 將值推入全域 `param_stack` |
| `CALL` | `sp++`，建立新 Frame，從 `param_stack` 搬參數，跳轉到函數入口 |
| `FORMAL` | 從 `incoming_args` 取值，在當前 Frame 建立區域變數 |
| `RET_VAL` | 保存回傳值，`sp--`，將值寫入呼叫者 Frame 的目標變數，跳回 `ret_pc` |
| `FUNC_BEG` | VM 直接跳過（函數不自動執行） |
| `FUNC_END` | 函數結尾，自然結束 |

### 4. 支援遞迴的關鍵

每次 `CALL` 都會 `sp++` 建立全新的 Frame：
- 每個 Frame 有自己的 `names[]` / `values[]`，變數完全隔離
- `ret_pc` 確保回傳後能精確回到正確的指令
- `ret_var` 確保回傳值能寫入正確的接收變數

這就是為什麼 `factorial(5)` 可以正確算出 `120`。
