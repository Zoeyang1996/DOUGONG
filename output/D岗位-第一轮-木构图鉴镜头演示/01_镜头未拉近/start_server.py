"""标准库本地服务器：只监听本机，无需安装第三方模块。"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
import webbrowser,sys
ROOT=Path(__file__).resolve().parent
class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-store');super().end_headers()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
page='开发预览.html' if '--source' in sys.argv else 'index.html'
from urllib.parse import quote
url='http://127.0.0.1:'+str(server.server_port)+'/'+quote(page)
print('本地地址：'+url,flush=True);print('请保持本窗口打开；Ctrl+C 停止。',flush=True);webbrowser.open(url)
try: server.serve_forever()
except KeyboardInterrupt: pass
finally: server.server_close()
