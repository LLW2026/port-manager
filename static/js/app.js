// 全局状态
let ports = [];
let hosts = [];
let listeningPorts = [];
let currentSort = 'project';
let currentHostId = 1;

// 获取本机IP
const LOCAL_IP = window.location.hostname;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadHosts();
    loadPorts();
    loadStats();

    // 搜索防抖
    let searchTimeout;
    document.getElementById('search-input').addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => loadPorts(), 300);
    });

    // 筛选
    document.getElementById('status-filter').addEventListener('change', () => loadPorts());
    document.getElementById('protocol-filter').addEventListener('change', () => loadPorts());

    // 排序
    document.getElementById('sort-select').addEventListener('change', (e) => {
        currentSort = e.target.value;
        renderPorts();
    });
});

// API 请求封装
async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '请求失败');
    }

    return response.json();
}

// ==================== 主机管理 ====================

// 加载主机列表
async function loadHosts() {
    try {
        hosts = await api('/api/hosts/');
        renderHostSelect();
    } catch (error) {
        console.error('加载主机列表失败:', error);
    }
}

// 渲染主机选择下拉框
function renderHostSelect() {
    const select = document.getElementById('host-select');
    select.innerHTML = hosts.map(h =>
        `<option value="${h.id}" ${h.id === currentHostId ? 'selected' : ''}>${escapeHtml(h.name)} (${h.hostname})</option>`
    ).join('');
}

// 切换主机
function onHostChange() {
    currentHostId = parseInt(document.getElementById('host-select').value);
    loadPorts();
    loadStats();
    updateHostStatus();
}

// 更新主机状态显示
function updateHostStatus() {
    const host = hosts.find(h => h.id === currentHostId);
    const statusEl = document.getElementById('host-status');
    if (host) {
        const statusMap = {
            'online': '🟢 在线',
            'offline': '🔴 离线',
            'unknown': '⚪ 未知'
        };
        statusEl.textContent = statusMap[host.status] || '⚪ 未知';
    }
}

// 测试主机连接
async function testHostConnection() {
    const host = hosts.find(h => h.id === currentHostId);
    if (!host) return;

    if (currentHostId === 1) {
        showToast('本机连接正常');
        return;
    }

    try {
        const result = await api(`/api/hosts/${currentHostId}/test`, { method: 'POST' });
        showToast(result.message);
        loadHosts();
    } catch (error) {
        showToast('测试失败: ' + error.message);
    }
}

// 显示主机管理模态框
async function showHostManager() {
    await loadHosts();
    renderHostList();
    document.getElementById('host-modal').classList.add('active');
}

// 渲染主机列表
function renderHostList() {
    const tbody = document.getElementById('host-list');
    tbody.innerHTML = hosts.map(host => {
        const statusClass = host.status === 'online' ? 'status-active' :
                           host.status === 'offline' ? 'status-inactive' : 'status-reserved';
        const statusText = host.status === 'online' ? '在线' :
                          host.status === 'offline' ? '离线' : '未知';
        const lastCheck = host.last_check ? formatDate(host.last_check) : '-';

        return `
            <tr>
                <td>${host.id}</td>
                <td><strong>${escapeHtml(host.name)}</strong></td>
                <td>${escapeHtml(host.hostname)}</td>
                <td>${host.port}</td>
                <td>${escapeHtml(host.username)}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>${lastCheck}</td>
                <td class="actions-cell">
                    <button class="btn btn-sm btn-secondary" onclick="testHost(${host.id})">测试</button>
                    <button class="btn btn-sm btn-secondary" onclick="editHost(${host.id})">编辑</button>
                    ${host.id !== 1 ? `<button class="btn btn-sm btn-danger" onclick="deleteHost(${host.id})">删除</button>` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

// 隐藏主机管理模态框
function hideHostModal() {
    document.getElementById('host-modal').classList.remove('active');
}

// 显示添加主机模态框
function showAddHostModal() {
    document.getElementById('host-modal-title').textContent = '添加主机';
    document.getElementById('host-id').value = '';
    document.getElementById('host-form').reset();
    document.getElementById('host-port').value = '22';
    document.getElementById('host-username').value = 'root';
    document.getElementById('host-edit-modal').classList.add('active');
}

// 编辑主机
function editHost(id) {
    const host = hosts.find(h => h.id === id);
    if (!host) return;

    document.getElementById('host-modal-title').textContent = '编辑主机';
    document.getElementById('host-id').value = host.id;
    document.getElementById('host-name').value = host.name;
    document.getElementById('host-hostname').value = host.hostname;
    document.getElementById('host-port').value = host.port;
    document.getElementById('host-username').value = host.username;
    document.getElementById('host-password').value = '';
    document.getElementById('host-ssh-key').value = host.ssh_key || '';
    document.getElementById('host-edit-modal').classList.add('active');
}

// 隐藏主机编辑模态框
function hideHostEditModal() {
    document.getElementById('host-edit-modal').classList.remove('active');
}

// 测试新主机连接
async function testNewHost() {
    const data = getHostFormData();
    if (!data.hostname) {
        showToast('请输入主机地址');
        return;
    }

    try {
        // 临时保存并测试
        const host = await api('/api/hosts/', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        const result = await api(`/api/hosts/${host.id}/test`, { method: 'POST' });
        showToast(result.message);

        // 删除临时记录
        await api(`/api/hosts/${host.id}`, { method: 'DELETE' });
    } catch (error) {
        showToast('测试失败: ' + error.message);
    }
}

// 获取主机表单数据
function getHostFormData() {
    return {
        name: document.getElementById('host-name').value,
        hostname: document.getElementById('host-hostname').value,
        port: parseInt(document.getElementById('host-port').value) || 22,
        username: document.getElementById('host-username').value || 'root',
        password: document.getElementById('host-password').value || null,
        ssh_key: document.getElementById('host-ssh-key').value || null
    };
}

// 提交主机表单
async function handleHostSubmit(event) {
    event.preventDefault();

    const id = document.getElementById('host-id').value;
    const data = getHostFormData();

    try {
        if (id) {
            await api(`/api/hosts/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showToast('更新成功');
        } else {
            await api('/api/hosts/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showToast('添加成功');
        }

        hideHostEditModal();
        await loadHosts();
        renderHostList();
    } catch (error) {
        showToast('操作失败: ' + error.message);
    }
}

// 测试主机
async function testHost(id) {
    try {
        const result = await api(`/api/hosts/${id}/test`, { method: 'POST' });
        showToast(result.message);
        await loadHosts();
        renderHostList();
    } catch (error) {
        showToast('测试失败: ' + error.message);
    }
}

// 删除主机
async function deleteHost(id) {
    const host = hosts.find(h => h.id === id);
    if (!host) return;

    if (!confirm(`确定要删除主机 "${host.name}" 吗？\n该主机的所有端口记录也会被删除。`)) {
        return;
    }

    try {
        await api(`/api/hosts/${id}`, { method: 'DELETE' });
        showToast('删除成功');
        await loadHosts();
        renderHostList();
        if (currentHostId === id) {
            currentHostId = 1;
            document.getElementById('host-select').value = '1';
            loadPorts();
            loadStats();
        }
    } catch (error) {
        showToast('删除失败: ' + error.message);
    }
}

// ==================== 端口扫描 ====================

// 扫描端口
async function scanRemotePorts() {
    const host = hosts.find(h => h.id === currentHostId);
    if (!host) return;

    try {
        listeningPorts = await api(`/api/hosts/${currentHostId}/ports`);
        document.getElementById('scan-title').textContent = `${host.name} - 监听端口`;
        renderScanResults();
        document.getElementById('scan-modal').classList.add('active');
    } catch (error) {
        showToast('扫描失败: ' + error.message);
    }
}

// 渲染扫描结果
function renderScanResults() {
    const tbody = document.getElementById('scan-list');
    const recordedPorts = new Set(ports.map(p => `${p.port}-${p.protocol}`));

    tbody.innerHTML = listeningPorts.map(lp => {
        const isRecorded = recordedPorts.has(`${lp.port}-${lp.protocol}`);
        return `
            <tr>
                <td><strong>${lp.port}</strong></td>
                <td>${lp.protocol}</td>
                <td>${lp.process_name || '-'}</td>
                <td>${lp.pid || '-'}</td>
                <td>${lp.address}</td>
                <td>
                    ${isRecorded
                        ? '<span class="scan-listed">✓ 已记录</span>'
                        : `<button class="btn btn-sm btn-primary" onclick="addFromScan(${lp.port}, '${lp.protocol}', '${lp.process_name || ''}')">添加记录</button>`
                    }
                </td>
            </tr>
        `;
    }).join('');
}

// 从扫描结果添加
function addFromScan(port, protocol, processName) {
    hideScanModal();
    showAddModal();
    document.getElementById('port-number').value = port;
    document.getElementById('port-protocol').value = protocol;
    document.getElementById('port-description').value = processName ? `进程: ${processName}` : '';
    document.getElementById('port-is-web').checked = isWebPort(port);
}

// 隐藏扫描模态框
function hideScanModal() {
    document.getElementById('scan-modal').classList.remove('active');
}

// ==================== 端口管理 ====================

// 加载端口列表
async function loadPorts() {
    const search = document.getElementById('search-input').value;
    const status = document.getElementById('status-filter').value;
    const protocol = document.getElementById('protocol-filter').value;

    const params = new URLSearchParams();
    params.append('host_id', currentHostId);
    if (search) params.append('search', search);
    if (status) params.append('status', status);
    if (protocol) params.append('protocol', protocol);
    params.append('sort_by', currentSort);

    try {
        ports = await api(`/api/ports/?${params}`);
        renderPorts();
        updateHostStatus();
    } catch (error) {
        showToast('加载失败: ' + error.message);
    }
}

// 加载统计
async function loadStats() {
    try {
        const params = new URLSearchParams();
        params.append('host_id', currentHostId);
        const stats = await api(`/api/ports/stats?${params}`);
        document.getElementById('stat-total').textContent = stats.total;
        document.getElementById('stat-active').textContent = stats.active;
        document.getElementById('stat-inactive').textContent = stats.inactive;
        document.getElementById('stat-reserved').textContent = stats.reserved;
        document.getElementById('stat-web').textContent = stats.web;
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 渲染端口列表
function renderPorts() {
    const tbody = document.getElementById('port-list');

    if (ports.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="empty-state">暂无端口记录，点击"添加端口"开始</td></tr>';
        return;
    }

    // 按项目分组时
    if (currentSort === 'project') {
        renderPortsByProject(tbody);
        return;
    }

    // 普通列表
    tbody.innerHTML = ports.map(port => createPortRow(port)).join('');
}

// 按项目分组渲染
function renderPortsByProject(tbody) {
    // 按项目分组
    const groups = {};
    ports.forEach(port => {
        const project = port.project || '未分组';
        if (!groups[project]) {
            groups[project] = [];
        }
        groups[project].push(port);
    });

    let html = '';

    // 按项目名排序
    const sortedProjects = Object.keys(groups).sort((a, b) => {
        if (a === '未分组') return 1;
        if (b === '未分组') return -1;
        return a.localeCompare(b);
    });

    sortedProjects.forEach(project => {
        // 项目标题行
        html += `<tr class="project-header">
            <td colspan="9">
                <span class="project-name">${escapeHtml(project)}</span>
                <span class="project-count">${groups[project].length} 个端口</span>
            </td>
        </tr>`;

        // 端口列表
        groups[project].forEach(port => {
            html += createPortRow(port);
        });
    });

    tbody.innerHTML = html;
}

// 创建端口行HTML
function createPortRow(port) {
    const isWeb = port.is_web === 1 || port.is_web === true;
    const webBadge = isWeb
        ? '<span class="web-badge web-yes" onclick="toggleWeb(' + port.id + ', false)" title="点击取消Web标记">Web</span>'
        : '<span class="web-badge web-no" onclick="toggleWeb(' + port.id + ', true)" title="点击标记为Web服务">-</span>';

    const visitBtn = isWeb
        ? `<button class="btn btn-sm btn-success" onclick="visitPort(${port.port})" title="访问 http://${LOCAL_IP}:${port.port}">访问</button>`
        : '';

    return `
        <tr>
            <td><strong>${port.port}</strong></td>
            <td>${port.protocol}</td>
            <td>${escapeHtml(port.description || '-')}</td>
            <td>${escapeHtml(port.project || '-')}</td>
            <td><span class="status-badge status-${port.status}">${getStatusLabel(port.status)}</span></td>
            <td>${webBadge}</td>
            <td>${escapeHtml(port.notes || '-')}</td>
            <td>${formatDate(port.updated_at)}</td>
            <td class="actions-cell">
                <button class="btn btn-sm btn-secondary" onclick="editPort(${port.id})">编辑</button>
                <button class="btn btn-sm btn-danger" onclick="deletePort(${port.id}, ${port.port})">删除</button>
                ${visitBtn}
            </td>
        </tr>
    `;
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 状态标签
function getStatusLabel(status) {
    const labels = {
        'active': '使用中',
        'inactive': '空闲',
        'reserved': '保留'
    };
    return labels[status] || status;
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;

    // 小于1小时显示"x分钟前"
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return minutes <= 1 ? '刚刚' : `${minutes}分钟前`;
    }

    // 小于24小时显示"x小时前"
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
    }

    // 其他显示日期
    return date.toLocaleDateString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 访问端口
function visitPort(port) {
    const url = `http://${LOCAL_IP}:${port}`;
    window.open(url, '_blank');
}

// 切换Web标记
async function toggleWeb(id, isWeb) {
    try {
        await api(`/api/ports/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ is_web: isWeb })
        });
        showToast(isWeb ? '已标记为Web服务' : '已取消Web标记');
        loadPorts();
        loadStats();
    } catch (error) {
        showToast('操作失败: ' + error.message);
    }
}

// 显示添加模态框
function showAddModal() {
    document.getElementById('modal-title').textContent = '添加端口';
    document.getElementById('port-id').value = '';
    document.getElementById('port-form').reset();
    document.getElementById('port-status').value = 'active';
    document.getElementById('port-is-web').checked = false;
    document.getElementById('port-modal').classList.add('active');
}

// 编辑端口
function editPort(id) {
    const port = ports.find(p => p.id === id);
    if (!port) return;

    document.getElementById('modal-title').textContent = '编辑端口';
    document.getElementById('port-id').value = port.id;
    document.getElementById('port-number').value = port.port;
    document.getElementById('port-protocol').value = port.protocol;
    document.getElementById('port-description').value = port.description || '';
    document.getElementById('port-project').value = port.project || '';
    document.getElementById('port-status').value = port.status;
    document.getElementById('port-is-web').checked = port.is_web === 1 || port.is_web === true;
    document.getElementById('port-notes').value = port.notes || '';
    document.getElementById('port-modal').classList.add('active');
}

// 隐藏模态框
function hideModal() {
    document.getElementById('port-modal').classList.remove('active');
}

// 提交表单
async function handleSubmit(event) {
    event.preventDefault();

    const id = document.getElementById('port-id').value;
    const data = {
        port: parseInt(document.getElementById('port-number').value),
        protocol: document.getElementById('port-protocol').value,
        description: document.getElementById('port-description').value || null,
        project: document.getElementById('port-project').value || null,
        status: document.getElementById('port-status').value,
        is_web: document.getElementById('port-is-web').checked,
        notes: document.getElementById('port-notes').value || null,
        host_id: currentHostId
    };

    try {
        if (id) {
            await api(`/api/ports/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showToast('更新成功');
        } else {
            await api('/api/ports/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showToast('添加成功');
        }

        hideModal();
        loadPorts();
        loadStats();
    } catch (error) {
        showToast('操作失败: ' + error.message);
    }
}

// 删除端口
async function deletePort(id, portNumber) {
    if (!confirm(`确定要删除端口 ${portNumber} 的记录吗？`)) {
        return;
    }

    try {
        await api(`/api/ports/${id}`, { method: 'DELETE' });
        showToast('删除成功');
        loadPorts();
        loadStats();
    } catch (error) {
        showToast('删除失败: ' + error.message);
    }
}

// 扫描本机端口（兼容旧接口）
async function scanPorts() {
    scanRemotePorts();
}

// 判断是否为常见Web端口
function isWebPort(port) {
    const webPorts = [80, 443, 8080, 8443, 8000, 8001, 8002, 8003, 8004, 8005,
        8010, 8015, 8020, 8025, 8030, 8035, 8040, 8045, 8050, 8060, 8070, 8080,
        8082, 8084, 8086, 8088, 8090, 8100, 8123, 8200, 8384, 8443, 8888,
        9000, 9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009, 9010, 9020,
        9030, 9040, 9050, 9060, 9070, 9080, 9090, 9100, 9200, 9300, 9443, 9876,
        9999, 10000, 3000, 3001, 3002, 3003, 4000, 4200, 4300, 5000, 5001, 5005,
        5173, 5500, 5555, 6000, 6060, 7000, 7070, 7777, 7890, 2080, 2082, 2083];
    return webPorts.includes(port);
}

// Toast 提示
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}
