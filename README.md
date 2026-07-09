# 企业合同管理系统

FastAPI + 原生 HTML/CSS/JS + JSON 文件存储，纯内部使用的合同全生命周期管理系统。

## 快速开始

### 1. 环境要求

- Python 3.10+
- Windows / Mac / Linux

### 2. 安装依赖

```bash
cd backend
pip install -e ".[dev]"
```

### 3. 启动系统（二选一）

**方式一：双击 `启动演示.bat`**（Windows）

自动安装依赖 → 创建演示数据 → 启动服务器 → 打开浏览器。

**方式二：命令行**

```bash
cd backend

# 创建演示数据（首次必做）
python -m app.demo_seed

# 启动服务器
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

浏览器打开 **http://localhost:8000**

### 4. 演示账号（密码统一: `demo123456`）

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `admin` | demo123456 |
| 经办人 | `张三` | demo123456 |
| 主管审批 | `李主管` | demo123456 |
| 法务审批 | `王法务` | demo123456 |

### 5. 运行测试

```bash
cd backend
pytest -v
```

## 依赖清单

| 包 | 用途 |
|----|------|
| `fastapi` | Web 框架 |
| `uvicorn` | ASGI 服务器 |
| `argon2-cffi` | 密码哈希 |
| `pydantic` | 数据校验 |
| `python-dotenv` | 环境变量 |
| `httpx` | HTTP 客户端（测试） |
| `pytest` | 测试框架 |
| `anyio` | 异步测试 |

全部通过 `pip install -e ".[dev]"` 一键安装。

## 功能模块

| 模块 | 说明 |
|------|------|
| 用户认证 | 登录/注销/会话管理（Argon2id + Cookie） |
| 合同管理 | 创建/编辑/提交审批/签订/归档 + 全文搜索 |
| 审批流转 | 两级审批（主管→法务），顺序控制 |
| 站内消息 | 审批通知 + 到期提醒 + 已读标记 |
| 模板管理 | 管理员预设合同模板（自定义字段） |
| 数据看板 | 合同统计/状态分布/审批通过率 |

## 项目结构

```
contract-system/
├── 启动演示.bat
├── backend/
│   ├── app/
│   │   ├── main.py              # 应用入口
│   │   ├── config.py            # 配置管理
│   │   ├── bootstrap.py         # 启动引导（自动创建管理员）
│   │   ├── demo_seed.py         # 演示数据预制脚本
│   │   ├── api/
│   │   │   ├── dependencies.py  # 权限注入
│   │   │   ├── errors.py        # 错误响应
│   │   │   └── routes/          # 路由层
│   │   │       ├── auth.py       # 认证
│   │   │       ├── contracts.py  # 合同
│   │   │       ├── internal.py   # 审批+消息
│   │   │       ├── templates.py  # 模板
│   │   │       └── admin.py      # 管理员
│   │   ├── services/            # 业务逻辑层
│   │   ├── schemas/             # Pydantic 模型
│   │   ├── repositories/        # 仓储层
│   │   ├── domain/              # 领域模型+枚举
│   │   ├── storage/             # JSON 文件存储
│   │   └── security/            # 密码+会话
│   ├── tests/                   # 测试套件（49条）
│   └── pyproject.toml           # 项目配置+依赖
├── frontend/
│   ├── pages/                   # HTML 页面
│   │   ├── public/              # 登录页
│   │   ├── handler/             # 经办人（工作台/合同）
│   │   ├── internal/            # 审批人（审批/消息）
│   │   └── admin/               # 管理员（看板/用户/模板）
│   └── assets/
│       └── js/                  # 前端 JS 模块
└── docs/                        # 文档
    ├── 需求分析.md
    ├── 概要设计.md
    ├── 实施计划.md
    ├── 测试报告.md
    └── 演示脚本.md
```

## API 一览

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/v1/auth/login` | 公开 | 登录 |
| POST | `/api/v1/auth/logout` | 登录 | 注销 |
| GET | `/api/v1/auth/me` | 登录 | 当前用户 |
| POST | `/api/v1/auth/register` | admin | 创建用户 |
| GET | `/api/v1/auth/approvers` | 登录 | 审批人列表 |
| GET | `/api/v1/contracts/` | 登录 | 合同列表 |
| POST | `/api/v1/contracts/` | handler | 创建合同 |
| GET | `/api/v1/contracts/{id}` | 登录 | 合同详情 |
| PUT | `/api/v1/contracts/{id}` | handler | 编辑合同 |
| POST | `/api/v1/contracts/{id}/submit` | handler | 提交审批 |
| POST | `/api/v1/contracts/{id}/sign` | handler | 确认签订 |
| POST | `/api/v1/contracts/{id}/archive` | handler/admin | 归档 |
| GET | `/api/v1/contracts/{id}/approvals` | 登录 | 审批记录 |
| POST | `/api/v1/contracts/{id}/approve` | approver | 审批通过 |
| POST | `/api/v1/contracts/{id}/reject` | approver | 审批驳回 |
| GET | `/api/v1/messages` | 登录 | 消息列表 |
| GET | `/api/v1/messages/unread-count` | 登录 | 未读数 |
| PATCH | `/api/v1/messages/{id}/read` | 登录 | 标记已读 |
| GET | `/api/v1/templates/` | 登录 | 模板列表 |
| POST | `/api/v1/templates/` | admin | 创建模板 |
| PUT | `/api/v1/templates/{id}` | admin | 编辑模板 |
| PATCH | `/api/v1/templates/{id}/status` | admin | 启停模板 |
| GET | `/api/v1/admin/users` | admin | 用户列表 |
| POST | `/api/v1/admin/users` | admin | 创建用户 |
| PATCH | `/api/v1/admin/users/{id}/status` | admin | 启停用户 |
| GET | `/api/v1/admin/stats` | admin | 数据看板 |

## 技术栈

- **后端**: Python 3.10+ / FastAPI / Pydantic v2
- **存储**: JSON 文件（原子写入 + 线程安全）
- **认证**: Argon2id 密码哈希 + HttpOnly Cookie Session
- **前端**: 原生 HTML/CSS/JS（ES Modules，无框架）
- **测试**: pytest + httpx + anyio
