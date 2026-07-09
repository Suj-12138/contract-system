# 企业合同管理系统

合同拟制、两级审批、模板管理、到期提醒、站内消息的单体 Web 应用。

## 功能边界

### 已实现

- 三类用户（经办人、审批人、管理员）注册/登录/退出
- 管理员初始化（环境变量配置，首次启动自动创建）
- 合同全生命周期管理（拟制 → 审批 → 签订 → 履约 → 归档）
- 固定两级审批（部门主管 → 法务）
- 合同模板管理（动态字段配置）
- 站内消息通知（审批结果、到期提醒）
- 审计日志（全操作记录）
- 数据看板（合同统计、审批通过率、到期预警）
- 关键词检索（合同标题 + 对手方）

### 不实现（MVP 范围外）

附件上传、外部通知（邮件/短信）、电子签章集成、高级权限（RBAC）、多条件筛选、批量操作、导出、合同取消/退回/重开、自动关闭、密码找回、多因素认证、验证码、关系型数据库迁移、多实例并发写入。

## 快速开始

### 环境要求

- Python 3.10+
- 现代浏览器（Chrome / Edge）

### 安装

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

### 配置初始管理员

```bash
# Windows PowerShell
$env:INITIAL_ADMIN_USERNAME="admin"
$env:INITIAL_ADMIN_EMAIL="admin@example.com"
$env:INITIAL_ADMIN_PASSWORD="your-secure-password"

# Linux / macOS
export INITIAL_ADMIN_USERNAME="admin"
export INITIAL_ADMIN_EMAIL="admin@example.com"
export INITIAL_ADMIN_PASSWORD="your-secure-password"
```

### 启动

```bash
cd backend
source .venv/Scripts/activate   # Linux/macOS: source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

访问 http://localhost:8000 ，自动跳转登录页。

### 运行测试

```bash
cd backend
pytest -v
```

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | FastAPI（单进程） |
| 前端 | 原生 HTML / CSS / JavaScript 多页面应用 |
| 持久化 | JSON 文件（`backend/data/store.json`），原子写入 + 线程锁 |
| 认证 | 服务端 Session，HttpOnly / SameSite=Lax Cookie，8 小时 TTL |
| 密码 | Argon2id 哈希 |
| 标识 | UUID v4；UTC ISO 8601 时间戳 |

## 架构分层

```
API 路由 → 应用服务 → 仓储协议 → JSON 存储适配器
```

## 合同状态机

```
draft → review → approved/rejected → signed → active → expired/renewed → archived
```

## 目录概览

```
backend/
  pyproject.toml
  app/
    main.py
    config.py
    bootstrap.py
    api/routes/       # auth, contracts, internal, templates, admin
    services/         # 业务用例编排
    domain/           # 枚举、状态机、模型工厂
    repositories/     # 仓储协议 + JSON 适配器
    schemas/          # Pydantic 请求/响应模型
    security/         # 密码哈希、会话管理
    storage/          # JSON 原子读写

frontend/
  pages/              # public/, handler/, internal/, admin/
  assets/css/         # 全局样式
  assets/js/          # 共享 JavaScript 模块
```
