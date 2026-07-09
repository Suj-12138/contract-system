/** 管理员功能 JS 模块 — 统计看板 + 用户管理 + 模板管理. */
import { apiRequest } from '/assets/js/api-client.js';

// ── 统计看板 ──────────────────────────────────────────────

export async function fetchStats() {
  const result = await apiRequest('/api/v1/admin/stats');
  if (result.error) {
    console.error('获取统计数据失败:', result.error);
    return null;
  }
  return result;
}

export function renderStatCards(stats, containerId = 'stats-container') {
  const container = document.getElementById(containerId);
  if (!container) return;

  const cards = [
    { number: stats.total_contracts ?? 0, label: '合同总数' },
    { number: `${((stats.approval_rate ?? 0) * 100).toFixed(1)}%`, label: '审批通过率' },
    { number: stats.expiring_soon ?? 0, label: '即将到期（30天）' },
    { number: stats.total_users ?? 0, label: '用户总数' },
    { number: stats.total_templates ?? 0, label: '模板总数' },
  ];

  container.innerHTML = `
    <div class="stats-grid">
      ${cards.map(c => `
        <div class="stat-card">
          <div class="number">${c.number}</div>
          <div class="label">${c.label}</div>
        </div>
      `).join('')}
    </div>
  `;
}

export function renderStatusDistribution(stats, containerId = 'status-distribution') {
  const container = document.getElementById(containerId);
  if (!container) return;

  const dist = stats.status_distribution ?? {};
  const labels = { draft: '草稿', review: '审批中', approved: '已批准', rejected: '已驳回', signed: '已签署', active: '生效中', expired: '已到期', archived: '已归档' };
  const rows = Object.entries(dist)
    .sort(([, a], [, b]) => b - a)
    .map(([status, count]) => `<tr><td>${labels[status] ?? status}</td><td>${count}</td></tr>`)
    .join('');

  const table = rows
    ? `<table><thead><tr><th>状态</th><th>数量</th></tr></thead><tbody>${rows}</tbody></table>`
    : '<p class="empty-state">暂无合同数据</p>';

  container.innerHTML = `<div class="card"><h3>合同状态分布</h3>${table}</div>`;
}

// ── 用户管理 ──────────────────────────────────────────────

export async function fetchUsers() {
  const result = await apiRequest('/api/v1/admin/users');
  if (result.error) {
    console.error('获取用户列表失败:', result.error);
    return [];
  }
  return result.users ?? [];
}

export function renderUserTable(users, containerId = 'user-table') {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!users.length) {
    container.innerHTML = '<p class="empty-state">暂无用户</p>';
    return;
  }

  container.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>用户名</th>
          <th>邮箱</th>
          <th>角色</th>
          <th>状态</th>
          <th>注册时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        ${users.map(u => `
          <tr>
            <td>${escapeHtml(u.username)}</td>
            <td>${escapeHtml(u.email)}</td>
            <td>${escapeHtml(u.role)}</td>
            <td><span class="badge ${u.is_active ? 'badge-active' : 'badge-inactive'}">${u.is_active ? '启用' : '禁用'}</span></td>
            <td>${formatDate(u.created_at)}</td>
            <td>
              <button class="btn-sm ${u.is_active ? 'btn-danger' : 'btn-primary'}" data-toggle-user="${u.id}" data-active="${u.is_active}">
                ${u.is_active ? '禁用' : '启用'}
              </button>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

export async function createUser(data) {
  const result = await apiRequest('/api/v1/admin/users', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return result;
}

export async function toggleUser(userId, isActive) {
  const result = await apiRequest(`/api/v1/admin/users/${userId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ is_active: isActive }),
  });
  return result;
}

// ── 模板管理 ──────────────────────────────────────────────

export async function fetchTemplates() {
  const result = await apiRequest('/api/v1/templates/');
  if (result.error) {
    console.error('获取模板列表失败:', result.error);
    return [];
  }
  return result.templates ?? [];
}

export function renderTemplateList(templates, containerId = 'template-list') {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!templates.length) {
    container.innerHTML = '<p class="empty-state">暂无模板</p>';
    return;
  }

  container.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>模板名称</th>
          <th>描述</th>
          <th>字段数</th>
          <th>状态</th>
          <th>创建时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        ${templates.map(t => `
          <tr>
            <td>${escapeHtml(t.name)}</td>
            <td>${escapeHtml(t.description ?? '')}</td>
            <td>${(t.fields_json ?? []).length}</td>
            <td><span class="badge ${t.is_active ? 'badge-active' : 'badge-inactive'}">${t.is_active ? '启用' : '停用'}</span></td>
            <td>${formatDate(t.created_at)}</td>
            <td>
              <button class="btn-sm btn-secondary" data-edit-template="${t.id}">编辑</button>
              <button class="btn-sm ${t.is_active ? 'btn-danger' : 'btn-primary'}" data-toggle-template="${t.id}" data-active="${t.is_active}">
                ${t.is_active ? '停用' : '启用'}
              </button>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

export async function saveTemplate(data, templateId) {
  const isUpdate = !!templateId;
  const path = isUpdate ? `/api/v1/templates/${templateId}` : '/api/v1/templates/';
  const method = isUpdate ? 'PUT' : 'POST';
  const result = await apiRequest(path, {
    method,
    body: JSON.stringify(data),
  });
  return result;
}

export async function toggleTemplate(templateId, isActive) {
  const result = await apiRequest(`/api/v1/templates/${templateId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ is_active: isActive }),
  });
  return result;
}

// ── 工具函数 ──────────────────────────────────────────────

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
