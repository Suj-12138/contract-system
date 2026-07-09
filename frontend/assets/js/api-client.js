const BASE = '';

export async function apiRequest(path, options = {}) {
  const config = {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };
  if (options.body && typeof options.body === 'string') {
    config.headers['Content-Type'] = 'application/json';
  }
  const resp = await fetch(BASE + path, config);
  if (resp.status === 401 && !path.includes('/auth/login')) {
    window.location.href = '/pages/public/login.html';
    return { error: { code: 'AUTHENTICATION_REQUIRED', message: '请先登录' } };
  }
  if (resp.status === 204) return {};
  const data = await resp.json();
  if (!resp.ok) {
    return { error: data.error || data.detail || { message: '请求失败' } };
  }
  return data;
}
