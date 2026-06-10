> 本專案由opencode撰寫

# 行程與檔案系統程式設計

## 概述

Linux 系統程式設計的核心圍繞著兩個主題：**行程管理**與**檔案輸出入**。兩者透過「檔案描述子」（file descriptor）這個抽象概念緊密結合——檔案、管道、裝置、socket 皆以整數 fd 表示，讓 I/O 操作有一致的介面。

---

## 一、行程管理

### 1.1 fork() — 行程分叉

`fork()` 複製當前行程，產生一個子行程。子行程是父行程的完整拷貝（程式碼、堆疊、堆、檔案描述子），但擁有獨立的位址空間。

```c
pid_t fork(void);
```

**回傳值：**
| 值 | 意義 |
|---|------|
| -1 | 失敗 |
| 0 | 子行程 |
| >0 | 父行程，回傳值為子行程 PID |

#### fork0: 基本分叉
```c
fork();
printf("%-5d : Hello world!\n", getpid());
```
一個 fork 產生 2 個行程，輸出 2 次。

#### fork1: 雙重分叉
```c
fork();
fork();
printf("%-5d : Hello world!\n", getpid());
```
兩個 fork 產生 4 個行程，輸出 4 次。

#### fork2: 辨識父子
```c
int n = fork();
if (n > 0)
    printf("I am parent, child pid=%d\n", n);
else
    printf("I am child, pid=%d\n", getpid());
```
透過回傳值區分父子，父行程的 `n` 為子 PID，子行程的 `n` 為 0。

#### fork3: 變數隔離
父子行程有獨立位址空間，子行程修改變數不影響父行程：

```
m=100, n fork 後：父 n=子PID, 子 n=0
父子各自修改 m，互不干擾。
```

### 1.2 exec() — 執行程式

`exec` 系列函數以新程式**取代**當前行程的程式碼、資料、堆疊，PID 不變。常見的有：

```c
execlp("ls", "ls", "-l", NULL);
execvp("ls", args);  // args = {"ls", "-l", NULL}
```

若 exec 成功，後續程式碼不再執行；若失敗則回傳 -1。

### 1.3 fork + exec — 經典搭配

```c
pid_t pid = fork();
if (pid == 0) {          // 子行程
    execvp(cmd, args);   // 取代為新程式
    perror("exec failed"); // 只會走到這裡（exec 失敗）
    exit(1);
} else {                  // 父行程
    wait(NULL);           // 等待子行程結束
}
```

### 1.4 wait() / waitpid() — 回收子行程

子行程結束後若父行程未回收，會變成**殭屍行程**（zombie）：

- `wait(&status)` — 阻塞等待**任一**子行程結束
- `waitpid(pid, &status, 0)` — 等待特定子行程

用完子行程後務必呼叫 wait，否則系統資源無法釋放。

### 1.5 system() — 簡便但昂貴

```c
system("ls -l");
```
內部等同 `fork + exec + wait`，但多了 shell 解析層，效率較低。

---

## 二、檔案輸出入

UNIX 的「一切都是檔案」，鍵盤、螢幕、一般檔案、管道都用檔案描述子操作。

### 2.1 標準檔案描述子

| 代號 | 名稱 | 巨集 | 用途 |
|------|------|------|------|
| 0 | stdin | STDIN_FILENO | 標準輸入（鍵盤） |
| 1 | stdout | STDOUT_FILENO | 標準輸出（螢幕） |
| 2 | stderr | STDERR_FILENO | 標準錯誤（螢幕） |

0, 1, 2 在程式啟動時自動開啟，指向終端機。

### 2.2 open() / close()

```c
int fd = open("file.txt", O_RDWR);          // 開啟已存在的檔案
int fd = open("file.txt", O_CREAT|O_RDWR, 0644); // 若不存在則建立
close(fd);
```

open 回傳**最小未使用**的檔案描述子。若先 close(0) 再 open，就會取得 0。

### 2.3 read() / write()

```c
char buf[128];
int n = read(fd, buf, sizeof(buf));  // 讀取，回傳實際讀入位元組
write(fd, buf, n);                   // 寫入
```

- read 回傳 0 代表 EOF
- read 回傳 -1 代表錯誤
- `read(0, buf, n)` 從 stdin 讀取
- `write(1, buf, n)` 輸出到 stdout
- `write(2, buf, n)` 輸出到 stderr

### 2.4 dup() / dup2() — 檔案描述子複製

```c
newfd = dup(oldfd);          // 複製到最小未使用的 fd
dup2(oldfd, newfd);          // 複製 oldfd 到 newfd（若 newfd 已開啟則先關閉）
```

重點：dup2 用於**重新導向**。

#### 實例：將 stdout 重新導向到檔案

```c
close(1);                          // 關閉 stdout
int fd = open("out.txt", O_RDWR);  // 此時 open 會取得 fd=1
printf("hello");                   // 實際上寫入 out.txt
```

等價寫法（更安全）：

```c
int fd = open("out.txt", O_RDWR);
dup2(fd, 1);   // 拷貝 fd 到 stdout（1）
close(fd);     // 可關閉原本的 fd
```

### 2.5 標準 I/O vs 系統呼叫

| 特性 | 標準 I/O (fopen/fread/fwrite) | 系統呼叫 (open/read/write) |
|------|------|------|
| 緩衝 | 有（使用者層緩衝） | 無（直接進核心） |
| 效能 | 大量小資料時較佳 | 少量大資料時較佳 |
| 移植性 | 高（ANSI C） | 低（POSIX） |

---

## 三、管線 (pipe)

pipe 建立單向資料通道，一端寫入、另一端讀出，常用於行程間通訊（IPC）。

```c
int fd[2];
pipe(fd);   // fd[0] = 讀端, fd[1] = 寫端
```

典型用法：fork 後父行程關閉讀端、子行程關閉寫端，形成單向通道。

### 實例：父寫子讀

```
fork
├─ 父行程：close(fd[0]), write(fd[1], data)
└─ 子行程：close(fd[1]), read(fd[0], buf)
```

### 實例：pipe + dup2 實作 ls | wc

```c
pipe(fd);
if (fork() == 0) {
    close(fd[0]);
    dup2(fd[1], 1);  // stdout → pipe 寫端
    execvp("ls", args);
} else {
    close(fd[1]);
    dup2(fd[0], 0);  // stdin → pipe 讀端
    execvp("wc", wc_args);
}
```

---

## 四、各系統呼叫心智圖

```
行程管理               檔案輸出入              管線 IPC
┌──────────┐         ┌──────────────┐       ┌─────────┐
│ fork()   │──複製──→│ 父子行程共用   │       │ pipe()  │
│ execvp() │──取代──→│ 檔案描述子表   │       │ dup2()  │
│ wait()   │──回收──→│ 避免殭屍      │       │ 重導向   │
│ system() │──封裝──→│ fork+exec+wait│       │ 父寫子讀 │
└──────────┘         └──────────────┘       └─────────┘
                            │
                     open/read/write/close
                            │
                    stdin(0) stdout(1) stderr(2)
```

---

## 五、範例程式列表

| 程式 | 說明 |
|------|------|
| `fork0.c` | 單次 fork，2 行程印 hello |
| `fork1.c` | 兩次 fork，4 行程印 hello |
| `fork2.c` | 用回傳值區分父子行程 |
| `fork3.c` | 父子變數隔離 |
| `exec_demo.c` | fork + execvp 執行程式 |
| `io1.c` | open/read/write/close 基本操作 |
| `echo1.c` | read(stdin) → write(stdout+stderr) |
| `fecho.c` | close + open 實作重導向 |
| `fecho2.c` | dup2 實作重導向 |
| `stderr.c` | stderr 重新導向到檔案 |
| `pipe_demo.c` | fork + pipe + dup2 = ls \| wc |
