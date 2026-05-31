import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple
from models import (
    Project, ProjectCreate, ProjectUpdate,
    PortAllocation, AllocationCreate,
    PortPool, PortPoolCreate
)


class AllocationDB:
    def __init__(self, db_path: str = "ports.db"):
        self.db_path = db_path
        self.init_tables()

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_tables(self):
        conn = self.get_conn()

        # 项目表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                host_id INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (host_id) REFERENCES hosts(id)
            )
        """)

        # 端口分配表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS port_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                host_id INTEGER NOT NULL DEFAULT 1,
                port INTEGER NOT NULL,
                protocol TEXT NOT NULL DEFAULT 'TCP',
                allocation_type TEXT NOT NULL DEFAULT 'auto',
                status TEXT NOT NULL DEFAULT 'allocated',
                description TEXT,
                allocated_at TEXT NOT NULL,
                released_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (host_id) REFERENCES hosts(id)
            )
        """)

        # 端口池表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS port_pools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                host_id INTEGER,
                start_port INTEGER NOT NULL,
                end_port INTEGER NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (host_id) REFERENCES hosts(id)
            )
        """)

        # 分配历史表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS allocation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                host_id INTEGER NOT NULL,
                port INTEGER NOT NULL,
                protocol TEXT NOT NULL DEFAULT 'TCP',
                action TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # 创建索引
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_allocations_host_port
            ON port_allocations(host_id, port, protocol)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_allocations_project
            ON port_allocations(project_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_allocations_status
            ON port_allocations(status)
        """)

        # 插入默认端口池
        cursor = conn.execute("SELECT COUNT(*) FROM port_pools")
        if cursor.fetchone()[0] == 0:
            now = datetime.now().isoformat()
            conn.execute(
                """INSERT INTO port_pools (name, host_id, start_port, end_port, description, created_at)
                   VALUES ('默认Web端口池', NULL, 8000, 8999, 'Web应用端口范围', ?)""",
                (now,)
            )
            conn.execute(
                """INSERT INTO port_pools (name, host_id, start_port, end_port, description, created_at)
                   VALUES ('默认应用端口池', NULL, 9000, 9999, '应用服务端口范围', ?)""",
                (now,)
            )

        conn.commit()
        conn.close()

    # ==================== 项目操作 ====================

    def get_projects(self, host_id: Optional[int] = None, status: Optional[str] = None) -> List[Project]:
        conn = self.get_conn()
        query = "SELECT * FROM projects WHERE 1=1"
        params = []

        if host_id is not None:
            query += " AND host_id = ?"
            params.append(host_id)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [Project(**dict(row)) for row in rows]

    def get_project(self, project_id: int) -> Optional[Project]:
        conn = self.get_conn()
        cursor = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Project(**dict(row))
        return None

    def create_project(self, data: ProjectCreate) -> Project:
        conn = self.get_conn()
        now = datetime.now().isoformat()

        cursor = conn.execute(
            """INSERT INTO projects (name, description, host_id, status, created_at, updated_at)
               VALUES (?, ?, ?, 'active', ?, ?)""",
            (data.name, data.description, data.host_id, now, now)
        )
        conn.commit()
        project_id = cursor.lastrowid
        conn.close()
        return self.get_project(project_id)

    def update_project(self, project_id: int, data: ProjectUpdate) -> Optional[Project]:
        conn = self.get_conn()
        now = datetime.now().isoformat()

        updates = []
        params = []

        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)
        if data.description is not None:
            updates.append("description = ?")
            params.append(data.description)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status)

        if not updates:
            conn.close()
            return self.get_project(project_id)

        updates.append("updated_at = ?")
        params.append(now)
        params.append(project_id)

        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, params)
        conn.commit()
        conn.close()
        return self.get_project(project_id)

    def delete_project(self, project_id: int) -> bool:
        conn = self.get_conn()
        # 释放该项目的所有端口
        now = datetime.now().isoformat()
        conn.execute(
            """UPDATE port_allocations SET status = 'released', released_at = ?
               WHERE project_id = ? AND status = 'allocated'""",
            (now, project_id)
        )
        # 记录历史
        cursor = conn.execute(
            """SELECT port, host_id FROM port_allocations WHERE project_id = ?""",
            (project_id,)
        )
        for row in cursor.fetchall():
            conn.execute(
                """INSERT INTO allocation_history (project_id, host_id, port, action, description, created_at)
                   VALUES (?, ?, ?, 'release', '项目删除自动回收', ?)""",
                (project_id, row['host_id'], row['port'], now)
            )

        # 删除项目
        cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    # ==================== 端口分配操作 ====================

    def get_allocations(
        self,
        host_id: Optional[int] = None,
        project_id: Optional[int] = None,
        status: str = "allocated"
    ) -> List[PortAllocation]:
        conn = self.get_conn()
        query = "SELECT * FROM port_allocations WHERE status = ?"
        params = [status]

        if host_id is not None:
            query += " AND host_id = ?"
            params.append(host_id)
        if project_id is not None:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " ORDER BY port ASC"
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [PortAllocation(**dict(row)) for row in rows]

    def get_allocation(self, allocation_id: int) -> Optional[PortAllocation]:
        conn = self.get_conn()
        cursor = conn.execute("SELECT * FROM port_allocations WHERE id = ?", (allocation_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return PortAllocation(**dict(row))
        return None

    def get_allocated_ports(self, host_id: int) -> set:
        """获取已分配的端口集合"""
        conn = self.get_conn()
        cursor = conn.execute(
            """SELECT port FROM port_allocations
               WHERE host_id = ? AND status = 'allocated'""",
            (host_id,)
        )
        ports = {row['port'] for row in cursor.fetchall()}
        conn.close()
        return ports

    def get_used_ports(self, host_id: int) -> set:
        """获取所有已使用的端口（包括手动录入的）"""
        conn = self.get_conn()
        cursor = conn.execute(
            "SELECT port FROM ports WHERE host_id = ?",
            (host_id,)
        )
        ports = {row['port'] for row in cursor.fetchall()}
        conn.close()
        return ports

    def get_available_ports(self, host_id: int, count: int = 10) -> List[int]:
        """获取可用端口列表"""
        # 获取端口池
        pools = self.get_port_pools(host_id)
        if not pools:
            pools = self.get_port_pools(None)  # 获取全局端口池

        # 获取已使用的端口
        allocated = self.get_allocated_ports(host_id)
        used = self.get_used_ports(host_id)
        all_used = allocated | used

        # 从端口池中找可用端口
        available = []
        for pool in pools:
            for port in range(pool.start_port, pool.end_port + 1):
                if port not in all_used and port not in available:
                    available.append(port)
                    if len(available) >= count:
                        return available

        return available

    def allocate_port(self, data: AllocationCreate) -> PortAllocation:
        """分配端口"""
        conn = self.get_conn()
        now = datetime.now().isoformat()

        if data.port:
            # 手动模式：指定端口
            # 检查端口是否已分配
            cursor = conn.execute(
                """SELECT id FROM port_allocations
                   WHERE host_id = ? AND port = ? AND status = 'allocated'""",
                (data.host_id, data.port)
            )
            if cursor.fetchone():
                conn.close()
                raise ValueError(f"端口 {data.port} 已被分配")

            cursor = conn.execute(
                """INSERT INTO port_allocations
                   (project_id, host_id, port, protocol, allocation_type, status, description, allocated_at)
                   VALUES (?, ?, ?, 'TCP', 'manual', 'allocated', ?, ?)""",
                (data.project_id, data.host_id, data.port, data.description, now)
            )
            conn.commit()
            allocation_id = cursor.lastrowid

            # 记录历史
            conn.execute(
                """INSERT INTO allocation_history (project_id, host_id, port, action, description, created_at)
                   VALUES (?, ?, ?, 'allocate', ?, ?)""",
                (data.project_id, data.host_id, data.port, data.description or '手动分配', now)
            )
            conn.commit()
            conn.close()

            return self.get_allocation(allocation_id)
        else:
            # 自动模式：从可用端口中分配
            available = self.get_available_ports(data.host_id, data.count)
            if len(available) < data.count:
                conn.close()
                raise ValueError(f"可用端口不足，需要 {data.count} 个，仅有 {len(available)} 个可用")

            allocations = []
            for port in available[:data.count]:
                cursor = conn.execute(
                    """INSERT INTO port_allocations
                       (project_id, host_id, port, protocol, allocation_type, status, description, allocated_at)
                       VALUES (?, ?, ?, 'TCP', 'auto', 'allocated', ?, ?)""",
                    (data.project_id, data.host_id, port, data.description, now)
                )
                allocation_id = cursor.lastrowid

                # 记录历史
                conn.execute(
                    """INSERT INTO allocation_history (project_id, host_id, port, action, description, created_at)
                       VALUES (?, ?, ?, 'allocate', ?, ?)""",
                    (data.project_id, data.host_id, port, data.description or '自动分配', now)
                )

                allocations.append(self.get_allocation(allocation_id))

            conn.commit()
            conn.close()

            # 如果只有一个，返回单个
            if len(allocations) == 1:
                return allocations[0]
            return allocations

    def release_port(self, host_id: int, port: int) -> bool:
        """释放端口"""
        conn = self.get_conn()
        now = datetime.now().isoformat()

        cursor = conn.execute(
            """UPDATE port_allocations
               SET status = 'released', released_at = ?
               WHERE host_id = ? AND port = ? AND status = 'allocated'""",
            (now, host_id, port)
        )

        if cursor.rowcount > 0:
            # 记录历史
            conn.execute(
                """INSERT INTO allocation_history (host_id, port, action, description, created_at)
                   VALUES (?, ?, 'release', '手动释放', ?)""",
                (host_id, port, now)
            )
            conn.commit()
            conn.close()
            return True

        conn.close()
        return False

    def release_allocation(self, allocation_id: int) -> bool:
        """释放端口分配"""
        allocation = self.get_allocation(allocation_id)
        if not allocation:
            return False
        return self.release_port(allocation.host_id, allocation.port)

    # ==================== 端口池操作 ====================

    def get_port_pools(self, host_id: Optional[int] = None) -> List[PortPool]:
        conn = self.get_conn()
        if host_id is not None:
            cursor = conn.execute(
                "SELECT * FROM port_pools WHERE host_id = ? OR host_id IS NULL ORDER BY start_port",
                (host_id,)
            )
        else:
            cursor = conn.execute("SELECT * FROM port_pools ORDER BY start_port")
        rows = cursor.fetchall()
        conn.close()
        return [PortPool(**dict(row)) for row in rows]

    def create_port_pool(self, data: PortPoolCreate) -> PortPool:
        conn = self.get_conn()
        now = datetime.now().isoformat()

        cursor = conn.execute(
            """INSERT INTO port_pools (name, host_id, start_port, end_port, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data.name, data.host_id, data.start_port, data.end_port, data.description, now)
        )
        conn.commit()
        pool_id = cursor.lastrowid
        conn.close()

        conn = self.get_conn()
        cursor = conn.execute("SELECT * FROM port_pools WHERE id = ?", (pool_id,))
        row = cursor.fetchone()
        conn.close()
        return PortPool(**dict(row))

    def delete_port_pool(self, pool_id: int) -> bool:
        conn = self.get_conn()
        cursor = conn.execute("DELETE FROM port_pools WHERE id = ?", (pool_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    # ==================== 历史记录 ====================

    def get_history(
        self,
        host_id: Optional[int] = None,
        project_id: Optional[int] = None,
        limit: int = 100
    ) -> List[dict]:
        conn = self.get_conn()
        query = "SELECT * FROM allocation_history WHERE 1=1"
        params = []

        if host_id is not None:
            query += " AND host_id = ?"
            params.append(host_id)
        if project_id is not None:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== 统计 ====================

    def get_stats(self, host_id: Optional[int] = None) -> dict:
        conn = self.get_conn()

        where = "WHERE status = 'allocated'"
        params = []
        if host_id is not None:
            where += " AND host_id = ?"
            params.append(host_id)

        total_allocated = conn.execute(
            f"SELECT COUNT(*) FROM port_allocations {where}", params
        ).fetchone()[0]

        # 按项目统计
        project_stats = conn.execute(
            f"""SELECT p.name, COUNT(*) as count
                FROM port_allocations pa
                LEFT JOIN projects p ON pa.project_id = p.id
                {where}
                GROUP BY pa.project_id
                ORDER BY count DESC""",
            params
        ).fetchall()

        # 今日分配数
        today = datetime.now().strftime("%Y-%m-%d")
        today_allocated = conn.execute(
            f"SELECT COUNT(*) FROM port_allocations {where} AND allocated_at LIKE ?",
            params + [f"{today}%"]
        ).fetchone()[0]

        # 总项目数
        total_projects = conn.execute(
            "SELECT COUNT(*) FROM projects WHERE status = 'active'"
        ).fetchone()[0]

        conn.close()

        return {
            "total_allocated": total_allocated,
            "total_projects": total_projects,
            "today_allocated": today_allocated,
            "project_stats": [dict(row) for row in project_stats]
        }
