from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from models import PortRecord, PortCreate, PortUpdate, ListeningPort
from database import Database
import psutil

router = APIRouter(prefix="/api/ports", tags=["ports"])
db = Database()


@router.get("/", response_model=List[PortRecord])
async def list_ports(
    host_id: Optional[int] = Query(default=None, description="主机ID"),
    search: Optional[str] = Query(default=None, description="搜索关键词"),
    status: Optional[str] = Query(default=None, description="状态筛选"),
    protocol: Optional[str] = Query(default=None, description="协议筛选"),
    sort_by: str = Query(default="port", description="排序方式: port, project, status, is_web, host")
):
    """获取端口列表"""
    return db.get_ports(search=search, status=status, protocol=protocol, host_id=host_id, sort_by=sort_by)


@router.get("/stats")
async def get_stats(
    host_id: Optional[int] = Query(default=None, description="主机ID")
):
    """获取端口统计信息"""
    return db.get_port_stats(host_id=host_id)


@router.get("/listening", response_model=List[ListeningPort])
async def get_listening_ports():
    """获取本机正在监听的端口"""
    listening_ports = []

    for conn in psutil.net_connections(kind='inet'):
        if conn.status == 'LISTEN':
            port = conn.laddr.port
            protocol = "TCP" if conn.type == 1 else "UDP"
            pid = conn.pid
            process_name = None

            if pid:
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            listening_ports.append(ListeningPort(
                port=port,
                protocol=protocol,
                pid=pid,
                process_name=process_name,
                address=conn.laddr.ip
            ))

    # 去重并排序
    seen = set()
    unique_ports = []
    for lp in sorted(listening_ports, key=lambda x: x.port):
        key = (lp.port, lp.protocol)
        if key not in seen:
            seen.add(key)
            unique_ports.append(lp)

    return unique_ports


@router.get("/{port_id}", response_model=PortRecord)
async def get_port(port_id: int):
    """获取单个端口记录"""
    port = db.get_port(port_id)
    if not port:
        raise HTTPException(status_code=404, detail="端口记录不存在")
    return port


@router.post("/", response_model=PortRecord)
async def create_port(port_data: PortCreate):
    """创建端口记录"""
    try:
        return db.create_port(port_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{port_id}", response_model=PortRecord)
async def update_port(port_id: int, port_data: PortUpdate):
    """更新端口记录"""
    try:
        port = db.update_port(port_id, port_data)
        if not port:
            raise HTTPException(status_code=404, detail="端口记录不存在")
        return port
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{port_id}")
async def delete_port(port_id: int):
    """删除端口记录"""
    if not db.delete_port(port_id):
        raise HTTPException(status_code=404, detail="端口记录不存在")
    return {"message": "删除成功"}
