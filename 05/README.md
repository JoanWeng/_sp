> 本專案由opencode撰寫

# 執行緒同步議題

## Thread (執行緒)
執行緒是行程中的輕量級執行單元，共享行程的記憶體空間（heap、全域變數），但擁有獨立的堆疊（stack）和暫存器。相較於行程（process），執行緒的建立、切換成本更低。

## Race Condition (競爭情況)
當多個執行緒同時存取共享資源，且至少有一個執行緒在寫入時，由於執行順序不確定，最終結果取決於執行緒的排程順序，稱為 race condition。

範例：`count++` 在組合語言層級包含讀取、加一、寫回三步驟。若兩個執行緒同時執行，可能發生：
- Thread A 讀取 count=5
- Thread B 讀取 count=5
- Thread A 寫回 count=6
- Thread B 寫回 count=6（應為 7，遺失一次更新）

## Mutex (互斥鎖)
Mutex 是一種同步機制，確保同時間只有一個執行緒能存取共享資源。執行緒在進入 critical section 前需 lock mutex，離開時 unlock。若 mutex 已被 lock，其他執行緒會阻塞等待。

```c
pthread_mutex_lock(&mutex);
// critical section
pthread_mutex_unlock(&mutex);
```

## Deadlock (死結)
當兩個以上的執行緒互相等待對方持有的資源，導致所有執行緒永久阻塞。發生條件（Coffman 條件）：
1. **Mutual Exclusion**：資源不可共享
2. **Hold and Wait**：持有資源的同時等待其他資源
3. **No Preemption**：資源不能被強制取回
4. **Circular Wait**：存在循環等待鏈

### 預防方法
- 固定資源取得順序（打破 Circular Wait）
- 使用 trylock 機制
- 一次取得所有資源

---

# 程式實作說明

## 1. bank.c — 銀行存提款模擬

### 目的
模擬同一個銀行帳戶被兩個執行緒分別執行 100,000 次存款（+1）和 100,000 次提款（-1），最終餘額必須維持正確（100,000），展示 mutex 如何解決 race condition。

### 核心機制

```c
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
```

`deposit()` 與 `withdraw()` 各自在迴圈中對 `balance` 操作前先 `pthread_mutex_lock()`，操作完後 `pthread_mutex_unlock()`。這保證了 `balance++` 與 `balance--` 這兩個 critical section **不會交錯執行**。

### 若不加鎖會發生什麼？
`balance++` 在 CPU 層級實際上為：
1. load balance → register
2. register + 1
3. store register → balance

若 Thread A 做完 step2 但還沒寫回時，Thread B 也讀到舊值，**兩次增量只生效一次**（lost update）。100,000 次迭代下最終餘額將會偏離 100,000。

---

## 2. producer_consumer.c — 生產者消費者問題

### 目的
實作 bounded buffer 經典同步問題，使用 mutex + condition variable 協調 2 個生產者與 2 個消費者。

### 資料結構

```c
int buffer[BUFFER_SIZE];  // 環形緩衝區（大小 5）
int in = 0, out = 0;      // 寫入 / 讀取指標
int count = 0;            // 緩衝區中 item 數量
```

三個同步原語：

| 變數 | 用途 |
|------|------|
| `mutex` | 保護 buffer、count 等共享資料 |
| `cond_full` | 生產者在此等待（緩衝區滿時） |
| `cond_empty` | 消費者在此等待（緩衝區空時） |

### 生產者流程

```
lock(mutex)
while (count == BUFFER_SIZE)          // 緩衝區滿 → 等待
    wait(cond_full, mutex)
put(item)                              // 放入資料
signal(cond_empty)                     // 通知消費者
unlock(mutex)
```

使用 `while` 而非 `if` 檢查條件是為了防止 **spurious wakeup**（虛假喚醒）。

### 消費者流程

```
lock(mutex)
while (count == 0)                     // 緩衝區空 → 等待
    wait(cond_empty, mutex)
item = get()                           // 取出資料
signal(cond_full)                      // 通知生產者
unlock(mutex)
```

### 執行結果範例

```
P0 -> 0 (count=1)     ← 生產者 0 放入第 0 項
P1 -> 0 (count=2)     ← 生產者 1 放入第 0 項
      C0 <- 0 (count=1)   ← 消費者 0 取出
      C1 <- 0 (count=0)   ← 消費者 1 取出
```

count 始終介於 0 ~ BUFFER_SIZE，不會 overflow 或 underflow。

---

## 3. dining_philosophers.c — 哲學家用餐問題

### 目的
模擬 5 位哲學家共享 5 支叉子的經典 deadlock 問題，並以**固定資源取得順序**預防 deadlock。

### 每人一支叉子的問題

若每位哲學家同時拿起左邊叉子，再等右邊叉子，所有人都只持有一支叉子且互相等待 → **deadlock**。

### 解決方案：依序取叉

```c
void pickup_forks_ordered(int i) {
    int first = i;
    int second = RIGHT;          // (i+1) % N
    if (first > second) {       // 編號大的先拿編號小的
        first = second;
        second = i;
    }
    pthread_mutex_lock(&forks[first]);
    pthread_mutex_lock(&forks[second]);
}
```

**關鍵**：所有哲學家都依照「叉子編號小 → 大」的固定順序取叉。

- 哲學家 4 的左叉 = 4，右叉 = 0 → 先拿 0 再拿 4
- 哲學家 0 的左叉 = 0，右叉 = 1 → 先拿 0 再拿 1

這打破了 **Circular Wait**（循環等待）：編號最大的叉子（4）不會被同時等待，至少有一位哲學家能取得兩支叉子。

### 哲學家生命週期

```
think → pickup_forks_ordered → eat → putdown_forks → think → ...
```

程式執行後無限循環，直到被外部強制終止（Ctrl+C 或 timeout）。

---

## 常見錯誤與重點整理

### Race Condition 示意
```c
// 錯誤：無保護
void* deposit(void* arg) {
    for (int i = 0; i < TIMES; i++) balance++;  // ← 非原子操作
}
```

### Deadlock 示意
```c
// 錯誤：所有哲學家先拿左邊再拿右邊
pthread_mutex_lock(&forks[i]);        // 左
pthread_mutex_lock(&forks[RIGHT]);    // 右
// → 每人拿一支，集體死鎖
```

### 正確同步原則
1. 共享資料一律用 mutex 保護
2. 條件變數檢查用 `while` 而非 `if`
3. 多資源取得時固定順序，避免 circular wait
4. 用完的資源盡快釋放（lock 範圍愈小愈好）
