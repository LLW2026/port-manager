from fastapi import APIRouter, HTTPException
from typing import List
from models import Host, HostCreate, HostUpdate, RemotePort
from database import Database
from ssh_manager import SSHManager

router = APIRouter(prefix="/api/hosts", tags=["hosts"])
db = Database()


@router.get("/", response_model=List[Host])
async def list_hosts():
    """获取主机列表"""
    return db.get_hosts()


@router.get("/{host_id}", response_model=Host)
async def get_host(host_id: int):
    """获取单个主机"""
    host = db.get_host(host_id)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")
    return host


@router.post("/", response_model=Host)
async def create_host(host_data: HostCreate):
    """添加主机"""
    try:
        return db.create_host(host_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{host_id}", response_model=Host)
async def update_host(host_id: int, host_data: HostUpdate):
    """更新主机"""
    host = db.update_host(host_id, host_data)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")
    return host


@router.delete("/{host_id}")
async def delete_host(host_id: int):
    """删除主机"""
    if host_id == 1:
        raise HTTPException(status_code=400, detail="不能删除本机")
    if not db.delete_host(host_id):
        raise HTTPException(status_code=404, detail="主机不存在")
    return {"message": "删除成功"}


@router.post("/{host_id}/test")
async def test_host(host_id: int):
    """测试主机连接"""
    host = db.get_host(host_id)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")

    success, message = SSHManager.test_connection(host)
    status = "online" if success else "offline"
    db.update_host_status(host_id, status)

    return {
        "success": success,
        "message": message,
        "status": status
    }


@router.get("/{host_id}/ports", response_model=List[RemotePort])
async def get_host_listening_ports(host_id: int):
    """获取主机监听端口"""
    host = db.get_host(host_id)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")

    if host_id == 1:
        # 本机使用psutil
        import psutil
        ports = []
        seen = set()
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN':
                port = conn.laddr.port
                protocol = "TCP" if conn.type == 1 else "UDP"
                key = (port, protocol)
                if key not in seen:
                    seen.add(key)
                    pid = conn.pid
                    process_name = None
                    if pid:
                        try:
                            process = psutil.Process(pid)
                            process_name = process.name()
                        except:
                            pass
                    ports.append(RemotePort(
                        host_id=1,
                        host_name="本机",
                        port=port,
                        protocol=protocol,
                        pid=pid,
                        process_name=process_name,
                        address=conn.laddr.ip
                    ))
        return sorted(ports, key=lambda x: x.port)
    else:
        # 远程主机使用SSH
        success, message = SSHManager.test_connection(host)
        if not success:
            db.update_host_status(host_id, "offline")
            raise HTTPException(status_code=400, detail=f"无法连接到主机: {message}")

        db.update_host_status(host_id, "online")
        return SSHManager.get_listening_ports(host)


@router.post("/{host_id}/ports/{port}/open")
async def open_port(host_id: int, port: int, protocol: str = "TCP"):
    """开放端口"""
    host = db.get_host(host_id)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")

    if host_id == 1:
        raise HTTPException(status_code=400, detail="本机端口请使用系统工具管理")

    success, message = SSHManager.open_port(host, port, protocol)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"message": message}


@router.post("/{host_id}/ports/{port}/close")
async def close_port(host_id: int, port: int, protocol: str = "TCP"):
    """关闭端口"""
    host = db.get_host(host_id)
    if not host:
        raise HTTPException(status_code=404, detail="主机不存在")

    if host_id == 1:
        raise HTTPException(status_code=400, detail="本机端口请使用系统工具管理")

    success, message = SSHManager.close_port(host, port, protocol)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"message": message}
