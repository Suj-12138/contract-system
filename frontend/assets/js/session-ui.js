import { apiRequest } from '/assets/js/api-client.js';

const ROLE_PAGES = {
  handler: '/pages/handler/dashboard.html',
  approver: '/pages/internal/approval.html',
  admin: '/pages/admin/stats.html',
};

export async function checkSession() {
  const result = await apiRequest('/api/v1/auth/me');
  if (result.error || !result.user) {
    window.location.href = '/pages/public/login.html';
    return null;
  }
  return result.user;
}

export function redirectByRole(role) {
  const page = ROLE_PAGES[role] || '/pages/handler/dashboard.html';
  window.location.href = page;
}

export function renderNav(user, containerId = 'nav-container') {
  const container = document.getElementById(containerId);
  if (!container) return;
  const links = [];
  if (user.role === 'handler') {
    links.push('<a href="/pages/handler/dashboard.html">工作台</a>');
    links.push('<a href="/pages/handler/contracts.html">我的合同</a>');
    links.push('<a href="/pages/handler/contract-form.html">新建合同</a>');
  }
  if (user.role === 'approver') {
    links.push('<a href="/pages/internal/approval.html">待审批</a>');
  }
  if (user.role === 'admin') {
    links.push('<a href="/pages/handler/dashboard.html">工作台</a>');
    links.push('<a href="/pages/handler/contracts.html">合同管理</a>');
    links.push('<a href="/pages/admin/templates.html">模板管理</a>');
    links.push('<a href="/pages/admin/users.html">用户管理</a>');
    links.push('<a href="/pages/admin/stats.html">数据看板</a>');
  }
  links.push('<a href="/pages/internal/messages.html">消息</a>');
  links.push(`<a href="#" id="logout-btn">退出(${user.username})</a>`);

  container.innerHTML = `<nav>${links.join(' | ')}</nav>`;

  document.getElementById('logout-btn')?.addEventListener('click', async (e) => {
    e.preventDefault();
    await apiRequest('/api/v1/auth/logout', { method: 'POST' });
    window.location.href = '/pages/public/login.html';
  });
}
