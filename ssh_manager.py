import paramiko
import socket
from typing import List, Optional, Tuple
from models import Host, RemotePort
import asyncio


class SSHManager:
    """SSH连接管理器"""

    @staticmethod
    def test_connection(host: Host) -> Tuple[bool, str]:
        """测试SSH连接"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                "hostname": host.hostname,
                "port": host.port,
                "username": host.username,
                "timeout": 10
            }

            if host.password:
                connect_kwargs["password"] = host.password
            if host.ssh_key:
                connect_kwargs["key_filename"] = host.ssh_key

            client.connect(**connect_kwargs)
            client.close()
            return True, "连接成功"
        except paramiko.AuthenticationException:
            return False, "认证失败"
        except paramiko.SSHException as e:
            return False, f"SSH错误: {str(e)}"
        except socket.timeout:
            return False, "连接超时"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

    @staticmethod
    def execute_command(host: Host, command: str) -> Tuple[bool, str]:
        """执行远程命令"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                "hostname": host.hostname,
                "port": host.port,
                "username": host.username,
                "timeout": 10
            }

            if host.password:
                connect_kwargs["password"] = host.password
            if host.ssh_key:
                connect_kwargs["key_filename"] = host.ssh_key

            client.connect(**connect_kwargs)
            stdin, stdout, stderr = client.exec_command(command, timeout=30)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            client.close()

            if error:
                return False, error
            return True, output
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_listening_ports(host: Host) -> List[RemotePort]:
        """获取远程主机监听端口"""
        # 使用netstat或ss命令获取监听端口
        commands = [
            "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null",
        ]

        for cmd in commands:
            success, output = SSHManager.execute_command(host, cmd)
            if success and output:
                return SSHManager._parse_port_output(output, host)

        return []

    @staticmethod
    def _parse_port_output(output: str, host: Host) -> List[RemotePort]:
        """解析端口输出"""
        ports = []
        seen = set()

        for line in output.split('\n'):
            line = line.strip()
            if not line or 'LISTEN' not in line:
                continue

            try:
                # 解析ss输出格式
                parts = line.split()
                if len(parts) >= 5:
                    local_address = parts[3] if 'ss' in line else parts[3]
                    process_info = parts[-1] if len(parts) > 5 else ""

                    # 提取端口号
                    if ':' in local_address:
                        addr, port_str = local_address.rsplit(':', 1)
                        port = int(port_str)

                        # 提取进程信息
                        pid = None
                        process_name = None
                        if 'pid=' in process_info:
                            try:
                                pid_part = process_info.split('pid=')[1].split(',')[0]
                                pid = int(pid_part)
                            except:
                                pass
                        if 'users:' in process_info:
                            try:
                                process_name = process_info.split('"')[1]
                            except:
                                pass

                        key = (port, 'TCP')
                        if key not in seen:
                            seen.add(key)
                            ports.append(RemotePort(
                                host_id=host.id,
                                host_name=host.name,
                                port=port,
                                protocol='TCP',
                                pid=pid,
                                process_name=process_name,
                                address=addr if addr else '0.0.0.0'
                            ))
            except (ValueError, IndexError):
                continue

        return sorted(ports, key=lambda x: x.port)

    @staticmethod
    def check_port_open(host: Host, port: int, protocol: str = 'TCP') -> bool:
        """检查远程端口是否开放"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM if protocol == 'TCP' else socket.SOCK_DGRAM)
            sock.settimeout(5)
            result = sock.connect_ex((host.hostname, port))
            sock.close()
            return result == 0
        except:
            return False

    @staticmethod
    def open_port(host: Host, port: int, protocol: str = 'TCP') -> Tuple[bool, str]:
        """开放端口（需要root权限）"""
        # 尝试使用ufw
        cmd = f"ufw allow {port}/{protocol.lower()}"
        success, output = SSHManager.execute_command(host, cmd)
        if success:
            return True, f"端口 {port}/{protocol} 已开放"

        # 尝试使用firewalld
        cmd = f"firewall-cmd --add-port={port}/{protocol.lower()} --permanent && firewall-cmd --reload"
        success, output = SSHManager.execute_command(host, cmd)
        if success:
            return True, f"端口 {port}/{protocol} 已开放"

        # 尝试使用iptables
        cmd = f"iptables -A INPUT -p {protocol.lower()} --dport {port} -j ACCEPT"
        success, output = SSHManager.execute_command(host, cmd)
        if success:
            return True, f"端口 {port}/{protocol} 已开放"

        return False, "无法开放端口，请检查权限和防火墙工具"

    @staticmethod
    def close_port(host: Host, port: int, protocol: str = 'TCP') -> Tuple[bool, str]:
        """关闭端口（需要root权限）"""
        # 尝试使用ufw
        cmd = f"ufw deny {port}/{protocol.lower()}"
        success, output = SSHManager.execute_command(host, cmd)
        if success:
            return True, f"端口 {port}/{protocol} 已关闭"

        # 尝试使用firewalld
        cmd = f"firewall-cmd --remove-port={port}/{protocol.lower()} --permanent && firewall-cmd --reload"
        success, output = SSHManager.execute_command(host, cmd)
        if success:
            return True, f"端口 {port}/{protocol} 已关闭"

        # 尝试使用iptables
        cmd = f"iptables -D INPUT -p {protocol.lower()} --dport {port} -j ACCEPT"
        success, output = SSHManager.execute_command(host, cmd)
        if success:
            return True, f"端口 {port}/{protocol} 已关闭"

        return False, "无法关闭端口，请检查权限和防火墙工具"
