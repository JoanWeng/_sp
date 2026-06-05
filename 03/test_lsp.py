#!/usr/bin/env python3
"""EmoLang LSP 伺服器整合測試 (參考 QiMing LSP 測試)"""

import subprocess
import json
import time
import os
import sys
import select


class LSPClient:
    def __init__(self, server_path):
        self.server_path = server_path
        self.proc = None
        self.buffer = b""

    def start(self):
        self.proc = subprocess.Popen(
            [sys.executable, self.server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        os.set_blocking(self.proc.stdout.fileno(), False)
        return self

    def send(self, message):
        body = json.dumps(message, ensure_ascii=False)
        body_bytes = body.encode("utf-8")
        header = f"Content-Length: {len(body_bytes)}\r\n\r\n"
        self.proc.stdin.write(header.encode() + body_bytes)
        self.proc.stdin.flush()

    def recv(self, timeout=3):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                chunk = self.proc.stdout.read(65536)
                if chunk:
                    self.buffer += chunk
            except BlockingIOError:
                pass

            if b"\r\n\r\n" in self.buffer:
                header, rest = self.buffer.split(b"\r\n\r\n", 1)
                for line in header.decode().split("\r\n"):
                    if line.startswith("Content-Length:"):
                        length = int(line.split(":")[1].strip())
                        if len(rest) >= length:
                            body = rest[:length].decode("utf-8")
                            self.buffer = rest[length:]
                            return json.loads(body)

            time.sleep(0.05)
        return None

    def stop(self):
        if self.proc:
            self.send({"jsonrpc": "2.0", "id": 999, "method": "shutdown"})
            self.send({"jsonrpc": "2.0", "method": "exit"})
            self.proc.wait(timeout=3)
            self.proc = None


def test_initialize():
    client = LSPClient("emolang_lsp.py").start()
    client.send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    resp = client.recv()
    assert resp is not None, "initialize 無回應"
    assert resp["id"] == 1
    caps = resp["result"]["capabilities"]
    assert "semanticTokensProvider" in caps
    assert "hoverProvider" in caps
    assert "documentSymbolProvider" in caps
    assert "completionProvider" in caps
    print("  ✓ initialize")
    return client


def test_did_open():
    client = LSPClient("emolang_lsp.py").start()
    client.send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    client.recv()

    client.send({
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": "file:///test.emo",
                "languageId": "emo",
                "version": 1,
                "text": "📢 42\n📝 name 🟰 \"test\"\n"
            }
        }
    })

    client.send({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "textDocument/semanticTokens/full",
        "params": {
            "textDocument": {"uri": "file:///test.emo"}
        }
    })
    resp = client.recv()
    assert resp is not None, "semanticTokens 無回應"
    data = resp["result"]["data"]
    assert len(data) > 0, "semanticTokens 資料不應為空"
    print(f"  ✓ didOpen + semanticTokens ({len(data)} 個整數)")
    client.stop()
    return data


def test_hover():
    client = LSPClient("emolang_lsp.py").start()
    client.send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    client.recv()

    client.send({
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": "file:///test.emo",
                "languageId": "emo",
                "version": 1,
                "text": "📢 42\n📢 \"hello\"\n📢 xyz\n🛠️ add(a, b) 👇\n    🔙 a ➕ b\n👆\n"
            }
        }
    })

    # Hover over 42 (line 0, char 3 = start of '42')
    client.send({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "textDocument/hover",
        "params": {
            "textDocument": {"uri": "file:///test.emo"},
            "position": {"line": 0, "character": 3}
        }
    })
    resp = client.recv()
    assert resp is not None
    hover = resp["result"]["contents"]["value"]
    assert "數值常數" in hover, f"Hover 應含數值常數，但得: {hover}"
    print(f"  ✓ hover over number: {hover}")

    # Hover over "hello" (line 1, char 4)
    client.send({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "textDocument/hover",
        "params": {
            "textDocument": {"uri": "file:///test.emo"},
            "position": {"line": 1, "character": 4}
        }
    })
    resp = client.recv()
    assert resp is not None
    hover = resp["result"]["contents"]["value"]
    assert "字串常數" in hover
    print(f"  ✓ hover over string: {hover}")

    # Hover over identifier (line 2, char 4 = 'xyz')
    client.send({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "textDocument/hover",
        "params": {
            "textDocument": {"uri": "file:///test.emo"},
            "position": {"line": 2, "character": 4}
        }
    })
    resp = client.recv()
    assert resp is not None
    hover = resp["result"]["contents"]["value"]
    assert "識別字" in hover
    print(f"  ✓ hover over identifier: {hover}")

    # AST hover over function definition "add" at line 3, char 3
    client.send({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "textDocument/hover",
        "params": {
            "textDocument": {"uri": "file:///test.emo"},
            "position": {"line": 3, "character": 3}
        }
    })
    resp = client.recv()
    assert resp is not None, "AST hover 無回應"
    hover = resp["result"]["contents"]["value"]
    assert "函式" in hover, f"AST hover 應含函式資訊，得: {hover}"
    print(f"  ✓ AST hover (function definition): {hover}")

    client.stop()


def test_document_symbol():
    client = LSPClient("emolang_lsp.py").start()
    client.send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    client.recv()

    client.send({
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": "file:///test.emo",
                "languageId": "emo",
                "version": 1,
                "text": "📦 x 🟰 10\n🛠️ add(a, b) 👇\n    🔙 a ➕ b\n👆\n📝 name 🟰 \"test\"\n"
            }
        }
    })

    client.send({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "textDocument/documentSymbol",
        "params": {
            "textDocument": {"uri": "file:///test.emo"}
        }
    })
    resp = client.recv()
    assert resp is not None
    symbols = resp["result"]
    assert len(symbols) > 0
    names = [s["name"] for s in symbols]
    assert "add" in names, f"應找到函數 add，但得: {names}"
    for s in symbols:
        r = s["range"]
        assert r["start"]["line"] != 0 or r["start"]["character"] != 0 or r["end"]["line"] != 0 or r["end"]["character"] != 0, \
            f"{s['name']} 的 range 不應全為 0"
    print(f"  ✓ documentSymbol: {names}")
    client.stop()


def test_completion():
    client = LSPClient("emolang_lsp.py").start()
    client.send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    client.recv()

    client.send({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "textDocument/completion",
        "params": {
            "textDocument": {"uri": "file:///test.emo"},
            "position": {"line": 0, "character": 0}
        }
    })
    resp = client.recv()
    assert resp is not None
    items = resp["result"]
    assert len(items) > 0
    labels = [i["label"] for i in items]
    assert "📢" in labels, f"應包含 📢, 但得: {labels}"
    assert "📦" in labels
    print(f"  ✓ completion ({len(items)} 個項目)")
    client.stop()


def test_did_change():
    client = LSPClient("emolang_lsp.py").start()
    client.send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    })
    client.recv()

    client.send({
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": "file:///test.emo",
                "languageId": "emo",
                "version": 1,
                "text": "📢 42"
            }
        }
    })

    client.send({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "textDocument/semanticTokens/full",
        "params": {
            "textDocument": {"uri": "file:///test.emo"}
        }
    })
    resp = client.recv()
    data_before = resp["result"]["data"]

    # Change content
    client.send({
        "jsonrpc": "2.0",
        "method": "textDocument/didChange",
        "params": {
            "textDocument": {"uri": "file:///test.emo", "version": 2},
            "contentChanges": [{"text": "📢 99\n📢 \"changed\"\n"}]
        }
    })

    client.send({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "textDocument/semanticTokens/full",
        "params": {
            "textDocument": {"uri": "file:///test.emo"}
        }
    })
    resp = client.recv()
    data_after = resp["result"]["data"]
    assert data_before != data_after, "變更後 semanticTokens 應不同"
    print("  ✓ didChange 正確更新語意突顯")
    client.stop()


def test_file_tests():
    test_dir = os.path.join(os.path.dirname(__file__), "tests")
    for fname in sorted(os.listdir(test_dir)):
        if fname.endswith(".emo"):
            path = os.path.join(test_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            uri = f"file:///{path}"

            client = LSPClient("emolang_lsp.py").start()
            client.send({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            })
            client.recv()

            client.send({
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {
                        "uri": uri, "languageId": "emo",
                        "version": 1, "text": code
                    }
                }
            })

            client.send({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "textDocument/semanticTokens/full",
                "params": {"textDocument": {"uri": uri}}
            })
            resp = client.recv()
            assert resp is not None
            data = resp["result"]["data"]
            assert len(data) > 0, f"{fname}: semanticTokens 不應為空"
            token_count = len(data) // 5
            print(f"  ✓ {fname}: {token_count} 個語意 token")
            client.stop()


def main():
    tests = [
        ("initialize", test_initialize),
        ("didOpen + semanticTokens", test_did_open),
        ("hover", test_hover),
        ("documentSymbol", test_document_symbol),
        ("completion", test_completion),
        ("didChange", test_did_change),
        ("tests/*.emo 檔案", test_file_tests),
    ]

    passed = 0
    failed = 0
    for name, func in tests:
        try:
            func()
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed += 1

    total = passed + failed
    print(f"\n{'='*40}")
    print(f"總計: {total} 項測試, {passed} 通過, {failed} 失敗")
    return failed


if __name__ == "__main__":
    sys.exit(main())
