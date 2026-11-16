#!/usr/bin/env python3
"""
本地预览服务器：静态文件 + 强制禁用缓存。

为什么要这个：浏览器对 ES 模块（import 链）的缓存很顽固，
`python3 -m http.server` 不返回 Cache-Control，改完代码刷新常常还是旧版本。
这里给所有响应加 no-store，刷新即为最新。

用法：
    cd web-exhibits && python3 serve.py 8123
"""
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):
        # 只打错误，避免刷屏
        if str(args[1] if len(args) > 1 else "") >= "400":
            super().log_message(fmt, *args)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8123
    host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    server = ThreadingHTTPServer((host, port), NoCacheHandler)
    print(f"serving http://{host}:{port}  (no-store)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
