import sqlite3
from datetime import datetime
from typing import List, Optional
from models import PortRecord, PortCreate, PortUpdate, Host, HostCreate, HostUpdate

# 常见Web端口列表
COMMON_WEB_PORTS = {
    80, 443, 8080, 8443, 8000, 8001, 8002, 8003, 8004, 8005,
    8010, 8011, 8012, 8013, 8014, 8015, 8020, 8021, 8022, 8023,
    8024, 8025, 8026, 8027, 8028, 8029, 8030, 8031, 8032, 8033,
    8034, 8035, 8036, 8037, 8038, 8039, 8040, 8041, 8042, 8043,
    8044, 8045, 8046, 8047, 8048, 8049, 8050, 8060, 8070, 8080,
    8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089, 8090,
    8100, 8110, 8120, 8123, 8130, 8140, 8150, 8160, 8170, 8180,
    8190, 8200, 8210, 8220, 8230, 8240, 8250, 8260, 8270, 8280,
    8290, 8300, 8310, 8320, 8330, 8340, 8350, 8360, 8370, 8380,
    8384, 8385, 8386, 8387, 8388, 8389, 8390, 8400, 8443, 8888,
    9000, 9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009,
    9010, 9020, 9030, 9040, 9050, 9060, 9070, 9080, 9090, 9100,
    9200, 9300, 9400, 9443, 9500, 9600, 9700, 9800, 9876, 9999,
    10000, 3000, 3001, 3002, 3003, 4000, 4001, 4200, 4201, 4300,
    4400, 4500, 5000, 5001, 5002, 5003, 5004, 5005, 5006, 5173,
    5174, 5500, 5555, 6000, 6001, 6060, 7000, 7001, 7070, 7777,
    7890, 9090, 9091, 2080, 2082, 2083, 2086, 2087, 2095, 2096,
}


def is_web_port(port: int) -> bool:
    """判断是否为常见Web端口"""
    return port in COMMON_WEB_PORTS


class Database:
    def __init__(self, db_path: str = "ports.db"):
        self.db_path = db_path
        self.init_db()
        self.migrate_db()

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_conn()

        # 主机表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hostname TEXT NOT NULL,
                port INTEGER NOT NULL DEFAULT 22,
                username TEXT NOT NULL DEFAULT 'root',
                password TEXT,
                ssh_key TEXT,
                status TEXT NOT NULL DEFAULT 'unknown',
                last_check TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 端口表（添加host_id字段）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL DEFAULT 1,
                port INTEGER NOT NULL,
                protocol TEXT NOT NULL DEFAULT 'TCP',
                description TEXT,
                project TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                notes TEXT,
                is_web INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (host_id) REFERENCES hosts(id),
                UNIQUE(host_id, port, protocol)
            )
        """)

        # 插入默认本机记录
        cursor = conn.execute("SELECT COUNT(*) FROM hosts WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            now = datetime.now().isoformat()
            conn.execute(
                """INSERT INTO hosts (id, name, hostname, port, username, status, created_at, updated_at)
                   VALUES (1, '本机', 'localhost', 22, 'root', 'online', ?, ?)""",
                (now, now)
            )

        conn.commit()
        conn.close()

    def migrate_db(self):
        """数据库迁移"""
        conn = self.get_conn()

        # 检查ports表是否有host_id字段
        cursor = conn.execute("PRAGMA table_info(ports)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'host_id' not in columns:
            conn.execute("ALTER TABLE ports ADD COLUMN host_id INTEGER NOT NULL DEFAULT 1")
            conn.commit()

        if 'is_web' not in columns:
            conn.execute("ALTER TABLE ports ADD COLUMN is_web INTEGER NOT NULL DEFAULT 0")
            conn.commit()

            # 自动标记Web端口
            cursor = conn.execute("SELECT id, port FROM ports")
            for row in cursor.fetchall():
                port_id, port_num = row
                if is_web_port(port_num):
                    conn.execute("UPDATE ports SET is_web = 1 WHERE id = ?", (port_id,))

            conn.commit()

        # 更新唯一约束
        try:
            conn.execute("DROP INDEX IF EXISTS sqlite_autoindex_ports_1")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ports_host_port_protocol ON ports(host_id, port, protocol)")
            conn.commit()
        except:
            pass

        conn.close()

    # ==================== 主机操作 ====================

    def get_hosts(self) -> List[Host]:
        conn = self.get_conn()
        cursor = conn.execute("SELECT * FROM hosts ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [Host(**dict(row)) for row in rows]

    def get_host(self, host_id: int) -> Optional[Host]:
        conn = self.get_conn()
        cursor = conn.execute("SELECT * FROM hosts WHERE id = ?", (host_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Host(**dict(row))
        return None

    def create_host(self, host_data: HostCreate) -> Host:
        conn = self.get_conn()
        now = datetime.now().isoformat()

        cursor = conn.execute(
            """INSERT INTO hosts (name, hostname, port, username, password, ssh_key, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'unknown', ?, ?)""",
            (host_data.name, host_data.hostname, host_data.port, host_data.username,
             host_data.password, host_data.ssh_key, now, now)
        )
        conn.commit()
        host_id = cursor.lastrowid
        conn.close()
        return self.get_host(host_id)

    def update_host(self, host_id: int, host_data: HostUpdate) -> Optional[Host]:
        conn = self.get_conn()
        now = datetime.now().isoformat()

        updates = []
        params = []

        if host_data.name is not None:
            updates.append("name = ?")
            params.append(host_data.name)
        if host_data.hostname is not None:
            updates.append("hostname = ?")
            params.append(host_data.hostname)
        if host_data.port is not None:
            updates.append("port = ?")
            params.append(host_data.port)
        if host_data.username is not None:
            updates.append("username = ?")
            params.append(host_data.username)
        if host_data.password is not None:
            updates.append("password = ?")
            params.append(host_data.password)
        if host_data.ssh_key is not None:
            updates.append("ssh_key = ?")
            params.append(host_data.ssh_key)

        if not updates:
            conn.close()
            return self.get_host(host_id)

        updates.append("updated_at = ?")
        params.append(now)
        params.append(host_id)

        query = f"UPDATE hosts SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, params)
        conn.commit()
        conn.close()
        return self.get_host(host_id)

    def delete_host(self, host_id: int) -> bool:
        if host_id == 1:
            return False  # 不能删除本机

        conn = self.get_conn()
        # 先删除该主机的所有端口记录
        conn.execute("DELETE FROM ports WHERE host_id = ?", (host_id,))
        cursor = conn.execute("DELETE FROM hosts WHERE id = ?", (host_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def update_host_status(self, host_id: int, status: str):
        conn = self.get_conn()
        now = datetime.now().isoformat()
        conn.execute("UPDATE hosts SET status = ?, last_check = ? WHERE id = ?", (status, now, host_id))
        conn.commit()
        conn.close()

    # ==================== 端口操作 ====================

    def get_ports(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        protocol: Optional[str] = None,
        host_id: Optional[int] = None,
        sort_by: str = "port"
    ) -> List[PortRecord]:
        conn = self.get_conn()
        query = "SELECT * FROM ports WHERE 1=1"
        params = []

        if host_id is not None:
            query += " AND host_id = ?"
            params.append(host_id)

        if search:
            query += " AND (port LIKE ? OR description LIKE ? OR project LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        if status:
            query += " AND status = ?"
            params.append(status)

        if protocol:
            query += " AND protocol = ?"
            params.append(protocol)

        # 排序
        if sort_by == "project":
            query += " ORDER BY CASE WHEN project IS NULL OR project = '' THEN 1 ELSE 0 END, project ASC, port ASC"
        elif sort_by == "status":
            query += " ORDER BY status ASC, port ASC"
        elif sort_by == "is_web":
            query += " ORDER BY is_web DESC, port ASC"
        elif sort_by == "host":
            query += " ORDER BY host_id ASC, port ASC"
        else:
            query += " ORDER BY port ASC"

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [PortRecord(**dict(row)) for row in rows]

    def get_port(self, port_id: int) -> Optional[PortRecord]:
        conn = self.get_conn()
        cursor = conn.execute("SELECT * FROM ports WHERE id = ?", (port_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return PortRecord(**dict(row))
        return None

    def create_port(self, port_data: PortCreate) -> PortRecord:
        conn = self.get_conn()
        now = datetime.now().isoformat()

        # 自动判断是否为Web端口
        is_web = port_data.is_web if port_data.is_web is not None else is_web_port(port_data.port)
        host_id = port_data.host_id or 1

        try:
            cursor = conn.execute(
                """INSERT INTO ports (host_id, port, protocol, description, project, status, notes, is_web, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    host_id,
                    port_data.port,
                    port_data.protocol,
                    port_data.description,
                    port_data.project,
                    port_data.status,
                    port_data.notes,
                    1 if is_web else 0,
                    now,
                    now
                )
            )
            conn.commit()
            port_id = cursor.lastrowid
            conn.close()
            return self.get_port(port_id)
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"端口 {port_data.port}/{port_data.protocol} 已存在")

    def update_port(self, port_id: int, port_data: PortUpdate) -> Optional[PortRecord]:
        conn = self.get_conn()
        now = datetime.now().isoformat()

        # 构建动态更新语句
        updates = []
        params = []

        if port_data.port is not None:
            updates.append("port = ?")
            params.append(port_data.port)
        if port_data.protocol is not None:
            updates.append("protocol = ?")
            params.append(port_data.protocol)
        if port_data.description is not None:
            updates.append("description = ?")
            params.append(port_data.description)
        if port_data.project is not None:
            updates.append("project = ?")
            params.append(port_data.project)
        if port_data.status is not None:
            updates.append("status = ?")
            params.append(port_data.status)
        if port_data.notes is not None:
            updates.append("notes = ?")
            params.append(port_data.notes)
        if port_data.is_web is not None:
            updates.append("is_web = ?")
            params.append(1 if port_data.is_web else 0)

        if not updates:
            conn.close()
            return self.get_port(port_id)

        updates.append("updated_at = ?")
        params.append(now)
        params.append(port_id)

        try:
            query = f"UPDATE ports SET {', '.join(updates)} WHERE id = ?"
            conn.execute(query, params)
            conn.commit()
            conn.close()
            return self.get_port(port_id)
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"端口冲突")

    def delete_port(self, port_id: int) -> bool:
        conn = self.get_conn()
        cursor = conn.execute("DELETE FROM ports WHERE id = ?", (port_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def get_port_stats(self, host_id: Optional[int] = None) -> dict:
        conn = self.get_conn()

        where = "WHERE 1=1"
        params = []
        if host_id is not None:
            where += " AND host_id = ?"
            params.append(host_id)

        total = conn.execute(f"SELECT COUNT(*) FROM ports {where}", params).fetchone()[0]
        active = conn.execute(f"SELECT COUNT(*) FROM ports {where} AND status = 'active'", params).fetchone()[0]
        inactive = conn.execute(f"SELECT COUNT(*) FROM ports {where} AND status = 'inactive'", params).fetchone()[0]
        reserved = conn.execute(f"SELECT COUNT(*) FROM ports {where} AND status = 'reserved'", params).fetchone()[0]
        web = conn.execute(f"SELECT COUNT(*) FROM ports {where} AND is_web = 1", params).fetchone()[0]

        conn.close()

        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "reserved": reserved,
            "web": web
        }
