## while 語法的處理 — 設計原理

### 1. 語法定義 (EBNF)

```ebnf
while_statement = "while" "(" expression ")" "{" { statement } "}" ;
```

### 2. 中間碼生成策略

`while` 迴圈的翻譯採用 **條件跳轉 + 無條件跳轉** 搭配 **Backpatching** 技術。

給定原始碼：

```c
while (i < 11) {
    sum = sum + i;
    i = i + 1;
}
```

編譯器產生的四元組序列如下：

```
000: IMM        11         -          t1         ; 載入常數 11
001: CMP_LT     i          t1         t2         ; i < 11 → t2
002: JMP_F      t2         -          ?          ; t2 為 false 則跳離迴圈
003: ADD        sum        i          t3         ; sum + i → t3
004: STORE      t3         -          sum        ; t3 存回 sum
005: IMM        1          -          t4         ; 載入常數 1
006: ADD        i          t4         t5         ; i + 1 → t5
007: STORE      t5         -          i          ; t5 存回 i
008: JMP        -          -          0          ; 無條件跳回指令 0 (迴圈開頭)
```

### 3. Backpatching（回填）技術

在解析 `while` 時，有兩個跳轉位置是未知的：

- **JMP_F 的目標地址**：條件為 false 時要跳出迴圈，但此時 body 尚未解析，不知道跳出後的指令位置。
- **JMP 的目標地址**：body 結束後要跳回條件判斷處，位置已知（就是 `expression()` 開始前的 `quad_count`）。

解法分三步：

1. **先發出 JMP_F，result 填 `?`**，記錄其索引 `jmp_idx`
2. **解析 body**，然後發出一條 `JMP` 跳回 `loop_start`（這條的 result 可直接設定）
3. **回填**：`JMP_F` 的 result 改為當前 `quad_count`（即迴圈後下一條指令的位置）

### 4. 虛擬機的執行流程

- **JMP_F**：當 `arg1` 值為 0（false）時，將 `pc` 設為 `result - 1`，跳出迴圈
- **JMP**：無條件將 `pc` 設為 `result - 1`，回到條件判斷處，形成迴圈

兩個指令都採 `pc = result - 1` 是因為主迴圈每次結束會 `pc++`，所以 -1 才能精確跳到目標。

### 5. 與 if 的對比

| 特性 | if | while |
|------|----|-------|
| 條件為 false | 跳過 body | 跳出迴圈 |
| 條件為 true | 執行 body 一次 | 重複執行 body |
| 跳轉指令 | 只有 JMP_F | JMP_F + JMP 回跳 |
