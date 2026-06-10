> 本書由Claude.ai編寫
  [對話連結](https://claude.ai/share/2f1c07fd-8ce8-43e5-953b-422a39893a12)

# 系統程式參考手冊

---

## 目錄

1. [系統程式概論](https://github.com/JoanWeng/_sp/blob/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/01-%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E6%A6%82%E8%AB%96/%E5%85%A7%E5%AE%B9.md)
2. [組合語言基礎](https://github.com/JoanWeng/_sp/blob/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/02-%E7%B5%84%E5%90%88%E8%AA%9E%E8%A8%80%E5%9F%BA%E7%A4%8E/%E5%85%A7%E5%AE%B9.md)
3. [暫存器與旗標](https://github.com/JoanWeng/_sp/blob/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/03-%E6%9A%AB%E5%AD%98%E5%99%A8%E8%88%87%E6%97%97%E6%A8%99/%E5%85%A7%E5%AE%B9.md)
4. [定址模式](https://github.com/JoanWeng/_sp/blob/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/04-%E5%AE%9A%E5%9D%80%E6%A8%A1%E5%BC%8F/%E5%85%A7%E5%AE%B9.md)
5. [指令集架構（ISA）](https://github.com/JoanWeng/_sp/tree/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/05-%E6%8C%87%E4%BB%A4%E9%9B%86%E6%9E%B6%E6%A7%8B%EF%BC%88ISA%EF%BC%89)
6. [堆疊與副程式](https://github.com/JoanWeng/_sp/blob/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/06-%E5%A0%86%E7%96%8A%E8%88%87%E5%89%AF%E7%A8%8B%E5%BC%8F/%E5%85%A7%E5%AE%B9.md)
7. [巨集處理器](https://github.com/JoanWeng/_sp/tree/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/07-%E5%B7%A8%E9%9B%86%E8%99%95%E7%90%86%E5%99%A8)
8. [組譯器設計](https://github.com/JoanWeng/_sp/blob/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/08-%E7%B5%84%E8%AD%AF%E5%99%A8%E8%A8%AD%E8%A8%88/%E5%85%A7%E5%AE%B9.md)
9. [連結器與載入器](https://github.com/JoanWeng/_sp/blob/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/09-%E9%80%A3%E7%B5%90%E5%99%A8%E8%88%87%E8%BC%89%E5%85%A5%E5%99%A8/%E5%85%A7%E5%AE%B9.md)
10. [作業系統介面](https://github.com/JoanWeng/_sp/blob/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/10-%E4%BD%9C%E6%A5%AD%E7%B3%BB%E7%B5%B1%E4%BB%8B%E9%9D%A2/%E5%85%A7%E5%AE%B9.md)
11. [編譯器概論](https://github.com/JoanWeng/_sp/blob/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/11-%E7%B7%A8%E8%AD%AF%E5%99%A8%E6%A6%82%E8%AB%96/%E5%85%A7%E5%AE%B9.md)
12. [開發工具實務](https://github.com/JoanWeng/_sp/blob/master/04/%E7%B3%BB%E7%B5%B1%E7%A8%8B%E5%BC%8F%E5%AE%8C%E5%85%A8%E5%8F%83%E8%80%83%E6%89%8B%E5%86%8A/12-%E9%96%8B%E7%99%BC%E5%B7%A5%E5%85%B7%E5%AF%A6%E5%8B%99/%E5%85%A7%E5%AE%B9.md)

---
 
## 章節概要
 
| 章 | 講義檔案 | 主要內容 | 習題檔案 |
|----|---------|---------|---------|
| 1 | `ch01_系統程式概論.md` | 系統程式定義、分類、程式執行流程 | — |
| 2 | `ch02_組合語言基礎.md` | 語法結構、區段、資料定義、兩遍組譯 | ex01 位置計數器、ex02 兩遍組譯、ex03 資料定義 |
| 3 | `ch03_暫存器與旗標.md` | 16 個通用暫存器、RFLAGS、條件跳躍 | ex01 暫存器、ex02 旗標、ex03 堆疊框架 |
| 4 | `ch04_定址模式.md` | 六大定址模式、SIB、LEA、ModRM | ex01 有效位址、ex02 ModRM/SIB、ex03 記憶體佈局 |
| 5 | `ch05_指令集架構.md` | 資料傳送、算術、邏輯、位元、控制流程、字串 | ex01 算術邏輯、ex02 控制流程、ex03 執行模擬 |
| 6 | `ch06_堆疊與副程式.md` | 堆疊框架、呼叫慣例、遞迴、尾遞迴最佳化 | ex01 堆疊框架、ex02 遞迴、ex03 堆疊安全 |
| 7 | `ch07_巨集處理器.md` | NASM 巨集、MNT/MDT、C 前置處理器 | ex01 巨集處理器、ex02 C 前置處理器 |
| 8 | `ch08_組譯器設計.md` | Pass 1/2 演算法、OPTAB、符號表、重定位表、ELF | ex01 兩遍組譯器 |
| 9 | `ch09_連結器與載入器.md` | 符號解析、重定位計算、靜態/動態連結、載入器 | ex01 連結器模擬 |
| 10 | `ch10_作業系統介面.md` | 系統呼叫、行程管理、記憶體管理、訊號、中斷 | ex01 OS 介面 |
| 11 | `ch11_編譯器概論.md` | 詞法/語法/語意分析、IR、最佳化、程式碼產生 | ex01 迷你編譯器 |
| 12 | `ch12_開發工具實務.md` | GCC、NASM、GDB、Make、objdump、strace | ex01 工具模擬 |
 
---
 
## 習題檔案清單
 
```
ch02_ex01_location_counter.py    位置計數器模擬
ch02_ex02_two_pass_assembler.py  兩遍組譯器模擬
ch02_ex03_data_directives.py     資料定義與記憶體佈局
 
ch03_ex01_registers.py           暫存器子部分存取（zero-extend 行為）
ch03_ex02_flags.py               旗標計算（CF/ZF/SF/OF/PF）
ch03_ex03_stack_frame.py         堆疊框架建立與銷毀
 
ch04_ex01_addressing.py          六大定址模式有效位址計算
ch04_ex02_modrm_sib.py           ModRM/SIB 位元組編碼與解碼
ch04_ex03_memory_layout.py       小端序記憶體佈局與 Hex Dump
 
ch05_ex01_instructions.py        算術/邏輯/移位指令完整模擬
ch05_ex02_control_flow.py        條件跳躍、REP 字串指令、迴圈模式
ch05_ex03_execution.py           旗標影響表、GCD 逐步執行、慣用法速查
 
ch06_ex01_stack_frame.py         函式呼叫四場景模擬（基本/區域變數/多參數/callee-saved）
ch06_ex02_recursion.py           遞迴呼叫樹視覺化（factorial/fib/hanoi/尾遞迴）
ch06_ex03_stack_security.py      堆疊平衡檢查、printf 呼叫慣例、Stack Canary
 
ch07_ex01_macro_processor.py     NASM 巨集處理器（MNT/MDT/唯一標號）
ch07_ex02_c_preprocessor.py      C 前置處理器（物件式/函式式/條件編譯）
 
ch08_ex01_assembler.py           完整兩遍組譯模擬（含重定位表與前向參考計算）
 
ch09_ex01_linker.py              連結器模擬（E/U/D 演算法、強弱符號、重定位計算）
 
ch10_ex01_os_interface.py        系統呼叫約定、行程生命週期、虛擬記憶體佈局、Page Fault
 
ch11_ex01_compiler.py            迷你編譯器（詞法→語法→AST→三位址碼→最佳化）
 
ch12_ex01_tools.py               GCC 管線、Makefile 增量建置、objdump 輸出、strace 追蹤
```
 
---
 
## 架構
 
```
硬體層
  └─ 第 3 章：暫存器與旗標
  └─ 第 4 章：定址模式
  └─ 第 5 章：指令集架構（ISA）
 
程式語言層
  └─ 第 2 章：組合語言基礎
  └─ 第 6 章：堆疊與副程式
  └─ 第 7 章：巨集處理器
 
工具鏈層
  └─ 第 8 章：組譯器設計
  └─ 第 9 章：連結器與載入器
  └─ 第 11 章：編譯器概論
  └─ 第 12 章：開發工具實務
 
系統層
  └─ 第 10 章：作業系統介面
 
概論
  └─ 第 1 章：系統程式概論
```