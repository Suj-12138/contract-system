# P4 — 模板 + 管理员功能（全栈）

- **角色**：P4
- **分支**：`feature/templates-admin`（基于 `main`）
- **远程**：`origin/feature/templates-admin`
- **负责模块**：合同模板 CRUD + 管理员用户管理 + 数据看板
- **开始日期**：2026-07-08
- **当前进度**：P4-DEV-04 / 10 完成

---

## 一、分支信息

```
main (29372e4)
  └── feature/templates-admin (bd74e84)  ← P4 当前分支
        └── feat: 模板 Schema

feature/auth-infra                       ← P1 分支（参考 API）
```

| 属性 | 值 |
|------|-----|
| 当前 commit | `bd74e84` |
| 基础 commit | `29372e4`（项目基线文档） |
| 文件数 | 1（`backend/app/schemas/templates.py`） |
| 未推送 | 无 |

---

## 二、模块范围

### 负责文件（10 个，不碰其他人的文件）

| # | 文件 | 内容 | 状态 |
|---|------|------|------|
| 1 | `backend/app/schemas/templates.py` | 模板 Pydantic Schema | ✅ DEV-01 完成 |
| 2 | `backend/app/services/template_service.py` | 模板业务逻辑 | ✅ DEV-02 完成 |
| 3 | `backend/app/services/admin_service.py` | 管理员业务逻辑 | ✅ DEV-03 完成 |
| 4 | `backend/app/api/routes/templates.py` | 模板路由（4 端点） | ✅ DEV-04 完成 |
| 5 | `backend/app/api/routes/admin.py` | 管理员路由（4 端点） | 待开发 |
| 6 | `frontend/assets/js/admin.js` | 管理页面 JS 模块 | 待开发 |
| 7 | `frontend/pages/admin/stats.html` | 数据看板页面 | 待开发 |
| 8 | `frontend/pages/admin/users.html` | 用户管理页面 | 待开发 |
| 9 | `frontend/pages/admin/templates.html` | 模板管理页面 | 待开发 |
| 10 | `frontend/assets/css/style.css` | 末尾追加管理样式 | 待追加 |

### 不碰的文件

- P1：认证/存储/仓储/公共 JS
- P2：合同业务
- P3：审批引擎和消息
- P5：测试代码

---

## 三、P1 依赖（11 项全部就绪）

| 依赖 | 文件 | 关键 API |
|------|------|----------|
| JsonRepository | `app/repositories/json_repository.py` | `list_active_templates()`, `list_all_templates()`, `find_template_by_id()`, `create_template()`, `update_template()` |
| JsonRepository（用户） | 同上 | `list_users()`, `find_user_by_username()`, `find_user_by_email()`, `find_user_by_id()`, `create_user()`, `update_user()` |
| JsonRepository（会话） | 同上 | `destroy_sessions_by_user()` |
| 权限注入 | `app/api/dependencies.py` | `get_current_user()`, `require_admin()` |
| 错误工具 | `app/api/errors.py` | `error()`, `not_found()`, `conflict()`, `forbidden()` |
| 密码哈希 | `app/security/passwords.py` | `hash_password()` |
| 模型工厂 | `app/domain/models.py` | `make_user(store, ...)`, `make_template(store, ...)` |
| 枚举 | `app/domain/enums.py` | `UserRole.ADMIN/HANDLER/APPROVER` |
| api-client.js | `frontend/assets/js/api-client.js` | `apiRequest(path, options)` |
| session-ui.js | `frontend/assets/js/session-ui.js` | `checkSession()`, `renderNav()`（已内置 admin 导航） |
| style.css | `frontend/assets/css/style.css` | stat-card / table / tag 基础样式 |

> **注意**：P1 代码在 `feature/auth-infra` 分支，尚未合并到 `main`。开发时参考该分支的 API 签名。

---

## 四、开发计划（10 DEV）

```
阶段 A — 后端 Schema + Service
  P4-DEV-01 ✅ 模板 Schema
  P4-DEV-02 ✅ 模板 Service
  P4-DEV-03 ✅ 管理员 Service

阶段 B — 后端 Route
  P4-DEV-04 ✅ 模板路由
  P4-DEV-05 ⬜ 管理员路由

阶段 C — 前端
  P4-DEV-06 ⬜ admin.js
  P4-DEV-07 ⬜ stats.html
  P4-DEV-08 ⬜ users.html
  P4-DEV-09 ⬜ templates.html
  P4-DEV-10 ⬜ CSS 追加
```

详细任务说明见 [P4开发任务清单](04-实施计划/P4开发任务清单.md)。

---

## 五、API 端点（P4 实现）

### 模板

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/v1/templates/` | 登录用户 | admin 全部 / 其他人仅启用 |
| POST | `/api/v1/templates/` | admin | 创建模板 |
| PUT | `/api/v1/templates/{id}` | admin | 编辑模板 |
| PATCH | `/api/v1/templates/{id}/status` | admin | 启用/停用 |

### 管理员

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/v1/admin/users` | admin | 用户列表 |
| POST | `/api/v1/admin/users` | admin | 创建用户 |
| PATCH | `/api/v1/admin/users/{id}/status` | admin | 启用/禁用 |
| GET | `/api/v1/admin/stats` | admin | 数据看板 |

---

## 六、关键架构模式

```python
# Service 构造（参考 P1 AuthService）
class TemplateService:
    def __init__(self, repo: JsonRepository):
        self._repo = repo

    def create(self, data, admin):
        template = make_template(
            self._repo._store,           # store 用于 new_id() / utcnow()
            data.name,
            data.description,
            [f.model_dump() for f in data.fields_json],
            admin["id"],
        )
        return self._repo.create_template(template)

# 路由工厂（参考 P1 auth.py）
def get_template_service(store=Depends(get_store)) -> TemplateService:
    return TemplateService(JsonRepository(store))

# main.py 注册（取消 P1 预留的注释）
# app.include_router(templates.router)   ← P4
# app.include_router(admin.router)       ← P4
```

---

## 七、开发环境

```bash
# 安装依赖（需要先切换到 feature/auth-infra 查看 P1 代码）
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows
pip install -e ".[dev]"

# 创建 .env（复制 .env.example）
# 启动
python -m uvicorn app.main:app --reload
```

---

## 八、Git 工作流

```bash
# 每完成一个 DEV：
git add <P4文件>
git commit -m "feat: <描述>"
git push origin feature/templates-admin

# P1 合并前确认所有代码已推送
```

**Commit 信息规范：**
1. `feat: 模板 Schema — TemplateCreate/TemplateUpdate/TemplateStatusUpdate/TemplateResponse`
2. `feat: 模板服务 — CRUD + 启用/停用`
3. `feat: 管理员服务 — 用户管理 + 数据看板统计`
4. `feat: 模板路由 — /api/v1/templates CRUD`
5. `feat: 管理员路由 — /api/v1/admin 用户管理 + 统计`
6. `feat: 模板+管理员前端 — stats.html + users.html + templates.html + admin.js`

---

## 九、文档索引

- **本仓库**：仅含 `P4-README.md` + 源代码
- **详细文档**（`D:\VScode-AI\together\docs\`，不入仓库）：
  - `README.md` — 全部文档导航
  - `04-实施计划/P4开发任务清单.md` — 10 个 DEV 详细说明（v0.3）
  - `05-开发过程/P4开发过程.md` — 开发日志与验证记录
  - `02-系统设计/系统设计说明书.md` — 整体架构
  - `01-需求分析/产品需求文档.md` — 需求基线
