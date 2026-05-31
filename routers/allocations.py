from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from models import (
    Project, ProjectCreate, ProjectUpdate,
    PortAllocation, AllocationCreate, AllocationRelease,
    PortPool, PortPoolCreate
)
from allocation_db import AllocationDB

router = APIRouter(prefix="/api", tags=["allocations"])
db = AllocationDB()


# ==================== 项目管理 ====================

@router.get("/projects", response_model=List[Project])
async def list_projects(
    host_id: Optional[int] = Query(default=None, description="主机ID"),
    status: Optional[str] = Query(default=None, description="状态筛选")
):
    """获取项目列表"""
    return db.get_projects(host_id=host_id, status=status)


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: int):
    """获取项目详情"""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.post("/projects", response_model=Project)
async def create_project(data: ProjectCreate):
    """创建项目"""
    try:
        project = db.create_project(data)

        # 如果需要自动分配端口
        if data.auto_allocate and data.port_count:
            alloc_data = AllocationCreate(
                project_id=project.id,
                host_id=data.host_id,
                count=data.port_count,
                is_web=data.is_web or False,
                description=f"项目 {data.name} 自动分配"
            )
            db.allocate_port(alloc_data)

        return project
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: int, data: ProjectUpdate):
    """更新项目"""
    project = db.update_project(project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    """删除项目（自动回收端口）"""
    if not db.delete_project(project_id):
        raise HTTPException(status_code=404, detail="项目不存在")
    return {"message": "项目已删除，端口已回收"}


# ==================== 端口分配 ====================

@router.get("/allocations", response_model=List[PortAllocation])
async def list_allocations(
    host_id: Optional[int] = Query(default=None, description="主机ID"),
    project_id: Optional[int] = Query(default=None, description="项目ID"),
    status: str = Query(default="allocated", description="状态")
):
    """获取端口分配列表"""
    return db.get_allocations(host_id=host_id, project_id=project_id, status=status)


@router.get("/allocations/available")
async def get_available_ports(
    host_id: int = Query(default=1, description="主机ID"),
    count: int = Query(default=10, description="数量")
):
    """获取可用端口列表"""
    available = db.get_available_ports(host_id, count)
    return {
        "host_id": host_id,
        "available_ports": available,
        "count": len(available)
    }


@router.post("/allocations", response_model=PortAllocation)
async def allocate_port(data: AllocationCreate):
    """分配端口"""
    try:
        result = db.allocate_port(data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/allocations/{allocation_id}")
async def release_allocation(allocation_id: int):
    """释放端口分配"""
    if not db.release_allocation(allocation_id):
        raise HTTPException(status_code=404, detail="分配记录不存在")
    return {"message": "端口已释放"}


@router.post("/allocations/release")
async def release_port(data: AllocationRelease):
    """释放指定端口"""
    if not db.release_port(data.host_id, data.port):
        raise HTTPException(status_code=404, detail="未找到该端口的分配记录")
    return {"message": f"端口 {data.port} 已释放"}


# ==================== 端口池 ====================

@router.get("/pools", response_model=List[PortPool])
async def list_port_pools(
    host_id: Optional[int] = Query(default=None, description="主机ID")
):
    """获取端口池列表"""
    return db.get_port_pools(host_id=host_id)


@router.post("/pools", response_model=PortPool)
async def create_port_pool(data: PortPoolCreate):
    """创建端口池"""
    try:
        return db.create_port_pool(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/pools/{pool_id}")
async def delete_port_pool(pool_id: int):
    """删除端口池"""
    if not db.delete_port_pool(pool_id):
        raise HTTPException(status_code=404, detail="端口池不存在")
    return {"message": "端口池已删除"}


# ==================== 历史记录 ====================

@router.get("/history")
async def get_history(
    host_id: Optional[int] = Query(default=None, description="主机ID"),
    project_id: Optional[int] = Query(default=None, description="项目ID"),
    limit: int = Query(default=100, description="返回数量")
):
    """获取分配历史"""
    return db.get_history(host_id=host_id, project_id=project_id, limit=limit)


# ==================== 统计 ====================

@router.get("/stats/allocations")
async def get_allocation_stats(
    host_id: Optional[int] = Query(default=None, description="主机ID")
):
    """获取分配统计"""
    return db.get_stats(host_id=host_id)
