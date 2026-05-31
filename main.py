import uvicorn
import socket
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from pathlib import Path

from routers import ports, hosts, allocations

# 获取当前文件所在目录
BASE_DIR = Path(__file__).resolve().parent


def get_local_ip():
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


app = FastAPI(title="端口管理工具", version="1.0.0")

# 静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 模板
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 注册路由
app.include_router(ports.router)
app.include_router(hosts.router)
app.include_router(allocations.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 35765

    print("=" * 50)
    print("端口管理工具")
    print("=" * 50)
    print(f"本机访问: http://localhost:{port}")
    print(f"局域网访问: http://{local_ip}:{port}")
    print(f"API 文档: http://{local_ip}:{port}/docs")
    print("=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=port)
