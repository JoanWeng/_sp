# 如何執行
gcc src/*.c -I include -o emolang

執行自己的程式碼:
./emolang 你的腳本(檔名要.emo)

# 以下是 EmoLang 與 C 語言、Python 在系統架構與語言特性上的對比：

## 1. 執行模型 (Execution Model)

  - C 語言：提前編譯 (AOT, Ahead-Of-Time)。原始碼直接編譯為特定硬體架構的原生機器碼 (Machine Code)，由 CPU
    直接執行。
  - Python：字節碼直譯 (Bytecode Interpretation)。原始碼先編譯為 Bytecode，再由虛擬機 (如 CPython VM)
    執行。
  - EmoLang：樹狀走訪直譯 (Tree-Walk Interpretation)。無 Bytecode 編譯階段，解析器建構抽象語法樹 (AST)
    後，求值引擎 (Evaluator) 直接以遞迴方式走訪 AST 節點並執行系統呼叫。

## 2. 型別系統 (Type System)

  - C 語言：靜態弱型別 (Static, Weakly Typed)。編譯期決定記憶體佈局，缺乏執行期型別檢查。
  - Python：動態強型別 (Dynamic, Strongly Typed)。物件具備嚴格的型別定義，但不允許隱式的不安全轉型
    (如整數與字串直接相加)。
  - EmoLang：動態弱型別 (Dynamic, Weakly Typed)。採用 Value 結構體封裝資料，執行期動態決議型別，並支援多型運算
    (Polymorphic Operations)，如自動將數字轉型並與字串進行拼接。

## 3. 記憶體管理 (Memory Management)

  - C 語言：開發者透過 OS 呼叫手動管理 (malloc / free)，需自行處理指標生命週期與記憶體破碎化。
  - Python：依賴引用計數 (Reference Counting) 與垃圾回收機制 (Garbage Collection) 自動釋放記憶體。
  - EmoLang：採用區域分配器 (Arena Allocator) 與靜態記憶體池 (Static Memory Pool)。AST
    與變數存放於預先分配的大型連續陣列中，無依賴 C 標準庫的動態配置，目前不具備自動垃圾回收。

## 4. 變數作用域與控制流 (Scope & Control Flow)

  - C 語言：以大括號 {} 定義區塊邊界，具備靜態詞法作用域 (Lexical Scoping)。
  - Python：以強制縮排 (Indentation) 定義區塊邊界。
  - EmoLang：採用 C 語言風格的詞法作用域，以符號 (👇/👆) 取代括號。支援呼叫堆疊 (Call Stack) 與區域變數隔離
    (call_depth 狀態機)，具備完整的 Scope 邊界。

## 5. 指標與底層抽象 (Pointer Abstraction)

  - C 語言：指標直接對應硬體的絕對實體/虛擬記憶體位址，可進行任意位元組運算，伴隨越界存取風險。
  - EmoLang：提供高度抽象的安全指標 (📍/🎯)。指標本質上是虛擬記憶體陣列 (memory[]) 的整數索引
    (Index)。保留了間接尋址能力，但消除了實體記憶體越界 (Segfault) 的風險。

## 6. 相依性與可攜性 (Dependencies)

  - C / Python：高度依賴作業系統與 C 標準函式庫 (libc, stdio, stdlib) 以實現 I/O 與底層互動。
  - EmoLang：裸機級別 (Bare Metal / Zero-Dependency)。完全剝離 C 標準庫，直接透過 POSIX 系統呼叫
    (System Calls, 如 sys_write, sys_read) 處理 I/O 與程序中斷，具備極高的底層移植性。
