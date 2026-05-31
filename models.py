from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class Protocol(str, Enum):
    TCP = "TCP"
    UDP = "UDP"


class PortStatus(str, Enum):
    ACTIVE = "active"       # 使用中
    INACTIVE = "inactive"   # 空闲
    RESERVED = "reserved"   # 保留


class HostStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class PortRecord(BaseModel):
    id: int
    host_id: int = 1  # 默认本机
    port: int
    protocol: str
    description: Optional[str] = None
    project: Optional[str] = None
    status: str
    notes: Optional[str] = None
    is_web: bool = False
    created_at: str
    updated_at: str


class PortCreate(BaseModel):
    port: int = Field(..., ge=1, le=65535, description="端口号")
    protocol: str = Field(default="TCP", description="协议")
    description: Optional[str] = Field(default=None, description="用途描述")
    project: Optional[str] = Field(default=None, description="关联项目")
    status: str = Field(default="active", description="状态")
    notes: Optional[str] = Field(default=None, description="备注")
    is_web: Optional[bool] = Field(default=None, description="是否Web服务")
    host_id: Optional[int] = Field(default=1, description="主机ID")


class PortUpdate(BaseModel):
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    protocol: Optional[str] = None
    description: Optional[str] = None
    project: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    is_web: Optional[bool] = None


class Host(BaseModel):
    id: int
    name: str
    hostname: str
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    status: str = "unknown"
    last_check: Optional[str] = None
    created_at: str
    updated_at: str


class HostCreate(BaseModel):
    name: str = Field(..., description="主机名称")
    hostname: str = Field(..., description="主机地址")
    port: int = Field(default=22, description="SSH端口")
    username: str = Field(default="root", description="用户名")
    password: Optional[str] = Field(default=None, description="密码")
    ssh_key: Optional[str] = Field(default=None, description="SSH密钥路径")


class HostUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key: Optional[str] = None


class ListeningPort(BaseModel):
    port: int
    protocol: str
    pid: Optional[int] = None
    process_name: Optional[str] = None
    address: str


class RemotePort(BaseModel):
    host_id: int
    host_name: str
    port: int
    protocol: str
    pid: Optional[int] = None
    process_name: Optional[str] = None
    address: str


# ==================== 项目管理 ====================

class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Project(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    host_id: int
    status: str = "active"
    created_at: str
    updated_at: str


class ProjectCreate(BaseModel):
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(default=None, description="项目描述")
    host_id: int = Field(default=1, description="主机ID")
    auto_allocate: Optional[bool] = Field(default=False, description="是否自动分配端口")
    port_count: Optional[int] = Field(default=1, description="自动分配端口数量")
    is_web: Optional[bool] = Field(default=False, description="是否Web项目")


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


# ==================== 端口分配 ====================

class AllocationStatus(str, Enum):
    ALLOCATED = "allocated"
    RELEASED = "released"
    RESERVED = "reserved"


class PortAllocation(BaseModel):
    id: int
    project_id: Optional[int] = None
    host_id: int
    port: int
    protocol: str = "TCP"
    allocation_type: str = "auto"  # auto / manual
    status: str = "allocated"
    description: Optional[str] = None
    allocated_at: str
    released_at: Optional[str] = None


class AllocationCreate(BaseModel):
    project_id: Optional[int] = Field(default=None, description="项目ID")
    host_id: int = Field(default=1, description="主机ID")
    port: Optional[int] = Field(default=None, description="指定端口（手动模式）")
    count: int = Field(default=1, description="分配数量（自动模式）")
    is_web: bool = Field(default=False, description="是否Web服务")
    description: Optional[str] = Field(default=None, description="用途描述")


class AllocationRelease(BaseModel):
    port: int
    host_id: int = 1


# ==================== 端口池 ====================

class PortPool(BaseModel):
    id: int
    name: str
    host_id: Optional[int] = None  # None表示全局
    start_port: int
    end_port: int
    description: Optional[str] = None
    created_at: str


class PortPoolCreate(BaseModel):
    name: str = Field(..., description="池名称")
    host_id: Optional[int] = Field(default=None, description="主机ID（null为全局）")
    start_port: int = Field(..., description="起始端口")
    end_port: int = Field(..., description="结束端口")
    description: Optional[str] = Field(default=None, description="描述")
