# Claude Code 启动 Prompt — 按角色

> 每个组员找到自己的角色，复制对应 Prompt，粘贴到 Claude Code 即可开始。

---

## 通用前置说明（所有人先读）

1. 从 Git 仓库 clone 项目，或拿到项目压缩包后解压
2. 用 VS Code 打开项目根目录（看到 `backend/` 和 `frontend/` 的那一层）
3. 在 VS Code 终端中执行：
   ```
   cd backend
   python -m venv .venv
   source .venv/Scripts/activate   # Linux/macOS: source .venv/bin/activate
   pip install -e ".[dev]"
   cp .env.example .env            # 创建本地环境配置（.env 不会被提交）
   ```
4. 确保参考项目 `enterticketsystem/` 也在本地，让 Claude Code 能读到它的代码风格
5. 打开 Claude Code，粘贴你对应角色的 Prompt

---

## P1：认证 + 基础设施

```
我是 5 人团队中的 P1，负责项目骨架和认证模块。

## 我的任务
按照实施计划中的 Task 1 到 Task 12，依次完成：
1. 项目骨架（pyproject.toml, .gitignore, README）
2. 配置模块（config.py）
3. JSON 存储层（storage/json_store.py）
4. 领域枚举与模型（domain/enums.py, domain/models.py）
5. Pydantic Schema（schemas/auth.py, schemas/users.py）
6. 密码哈希 + 会话管理（security/passwords.py, security/sessions.py）
7. 错误响应 + 权限依赖（api/errors.py, api/dependencies.py）
8. 仓储协议 + JSON 实现（repositories/protocols.py, repositories/json_repository.py）
9. 认证服务（services/auth_service.py）
10. 认证路由（api/routes/auth.py）
11. 应用入口 + 启动引导（main.py, bootstrap.py）
12. 登录页面 + 公共 JS/CSS（frontend/pages/public/login.html, frontend/assets/）

## 参考资料
- 完整架构和代码约定在《企业合同管理系统-概要设计.md》第五、六、八、十二章
- 实施计划在《企业合同管理系统-实施计划.md》Task 1-12（含完整参考代码）
- 参考项目 enterticketsystem/ 的架构模式——存储层、认证、前端 JS 模块都直接复用它的模式

## 约束
- Python 3.10+, Pydantic v2, FastAPI
- 前端原生 HTML/CSS/JS，ES Modules，无框架
- 所有实体 ID 用 UUID v4，时间戳 UTC ISO 8601
- 密码用 Argon2id
- Cookie: HttpOnly, SameSite=Lax, 8小时TTL
- 数据文件 backend/data/store.json，gitignore 掉
- 错误响应格式: {"error": {"code": "...", "message": "中文描述"}}
- 我的 main.py 要预留 P2/P3/P4 的路由注册位置（用注释标记）
- 仓储层写完整——P2/P3/P4 只调我的 JsonRepository 方法，不直接操作 JSON 文件
- 前端 api-client.js 和 session-ui.js 是我写的，P2/P3/P4 的页面会 import 它们

先不用写测试，P5 负责测试。

请按 Task 编号顺序，一个一个完成。每个 Task 完成后告诉我，等我确认再继续下一个。
```

---

## P2：合同业务（全栈）

```
我是 5 人团队中的 P2，负责合同业务模块（后端+前端）。

## 前提
P1 已经建好了项目骨架，包括 JSON 存储层、仓储（JsonRepository）、认证模块、公共 JS（api-client.js, session-ui.js）。
我需要基于这些基础设施开发合同模块。

## 我的任务
按照实施计划 Task 13-16：

### 后端
1. schemas/contracts.py — ContractCreate, ContractUpdate, ContractResponse
2. services/contract_service.py — 合同 CRUD + 状态机 + 全文检索 + 审计日志
3. api/routes/contracts.py — 合同路由（7个端点）

### 前端
4. pages/handler/dashboard.html — 工作台首页（我的合同数、待审批数、即将到期数、快捷入口）
5. pages/handler/contracts.html — 合同列表（状态筛选标签 + 关键词搜索 + 分页）
6. pages/handler/contract-detail.html — 合同详情（内容 + 审批进度 + 操作按钮）
7. pages/handler/contract-form.html — 新建合同（模板选择 + 动态表单）
8. pages/handler/contract-edit.html — 编辑合同（预填数据，仅 draft/rejected 可编辑）
9. assets/js/handler.js — 合同页面 JS 逻辑

## 我需要知道的关键接口

### JsonRepository 已有的方法（P1 提供，我直接调用）
- create_contract(contract) / find_contract_by_id(id) / update_contract(id, updates)
- list_contracts_by_handler(handler_id, status) / list_all_contracts(status) / list_contracts_for_approver(approver_id)
- search_contracts(keyword, user_id, role)
- create_audit_log(log) / list_audit_logs_by_target(target_type, target_id)

### 状态机（在 domain/enums.py，P1 已定义）
ContractStatus: DRAFT → REVIEW → APPROVED/REJECTED → SIGNED → ACTIVE → EXPIRED/RENEWED → ARCHIVED

### 前端公共模块（P1 提供，我不改）
- api-client.js: export async function apiRequest(path, options) — 统一请求封装，自动处理 401
- session-ui.js: export async function checkSession() / export function renderNav(user, containerId)

### 我的页面模式
每个 HTML 页面：
```html
<script type="module">
import { checkSession, renderNav } from '/assets/js/session-ui.js';
import { apiRequest } from '/assets/js/api-client.js';
const user = await checkSession();
renderNav(user);
// 页面业务逻辑
</script>
```

## 参考
- 实施计划 Task 13-16 含完整代码
- 概要设计第八、九章
- 参考 enterticketsystem/ 的页面结构和 JS 模块风格

先不用写测试，P5 负责。

请按顺序完成：先 schemas → services → routes → 再 5 个前端页面。
```

---

## P3：审批引擎 + 消息（全栈）

```
我是 5 人团队中的 P3，负责审批引擎和消息模块（后端+前端）。

## 前提
P1 已经建好了项目骨架，P2 已经（或正在）写合同模块。
P2 的 contract_service.submit() 提交审批后需要触发我的 approval_service.create_approval_records()。
我和 P2 约定：P2 的 submit 方法中调用我的函数，或者我在我的路由中独立处理。

## 我的任务
按照实施计划 Task 17-21：

### 后端
1. schemas/messages.py — MessageResponse
2. services/approval_service.py — 两级审批逻辑（创建审批记录、逐级通过/驳回、通知）
3. services/message_service.py — 消息 CRUD + 到期提醒扫描
4. api/routes/internal.py — 审批路由 + 消息路由（6个端点）

### 前端
5. pages/internal/approval.html — 待审批合同列表 + 通过/驳回操作 + 审批意见
6. pages/internal/messages.html — 未读/已读标签切换 + 消息列表 + 点击跳转
7. assets/js/internal.js — 审批/消息页面 JS 逻辑

## 审批规则（核心）
- 合同提交审批 → 按 approver_1_id → approver_2_id 创建两条 approval_records（decision=pending）
- 一级审批通过后，二级才能审批
- 任一级驳回 → 合同状态 → rejected，通知经办人
- 两级都通过 → 合同状态 → approved，通知经办人
- 审批人只能批自己的节点，不能越级

## JsonRepository 已有的方法（P1 提供）
- find_contract_by_id / update_contract
- create_approval_record / find_approvals_by_contract / update_approval_record
- list_contracts_for_approver
- create_message / list_messages_by_user / mark_message_read / unread_message_count

## 前端公共模块（P1 提供）
- api-client.js: apiRequest()
- session-ui.js: checkSession(), renderNav()

## 参考
- 实施计划 Task 17-21 含完整代码（审批逻辑已写清楚）
- 概要设计第七、八、十章
- 参考 enterticketsystem/ 的页面结构

请按顺序完成：schemas → approval_service → message_service → routes → 前端页面。
```

---

## P4：模板 + 管理员功能（全栈）

```
我是 5 人团队中的 P4，负责模板管理和管理员功能（后端+前端）。

## 前提
P1 已经建好了项目骨架，JsonRepository 已包含模板和管理员相关方法。
我需要基于这些基础设施开发。

## 我的任务
按照实施计划 Task 22-26：

### 后端
1. schemas/templates.py — TemplateCreate, TemplateUpdate, TemplateStatusUpdate
2. services/template_service.py — 模板 CRUD + 启停
3. services/admin_service.py — 用户管理 + 数据看板统计
4. api/routes/templates.py — 模板路由（4个端点）
5. api/routes/admin.py — 管理员路由（4个端点）

### 前端
6. pages/admin/templates.html — 模板列表 + 新建/编辑表单 + 启用/停用
7. pages/admin/users.html — 用户列表 + 创建用户表单 + 启用/禁用
8. pages/admin/stats.html — 统计卡片（合同总数/审批通过率/到期数/用户数/模板数）
9. assets/js/admin.js — 管理页面 JS 逻辑

## 模板字段定义（核心）
fields_json 格式：
```json
[
  {"label": "甲方", "type": "text", "required": true},
  {"label": "合同金额", "type": "number", "required": false},
  {"label": "交付日期", "type": "date", "required": true},
  {"label": "主要条款", "type": "textarea", "required": true}
]
```
type 支持: text, number, date, textarea

## JsonRepository 已有的方法（P1 提供）
- 模板: list_active_templates / list_all_templates / find_template_by_id / create_template / update_template
- 用户: list_users / find_user_by_username / find_user_by_email / find_user_by_id / create_user / update_user / list_users_by_role / destroy_sessions_by_user
- 统计: 直接读 store._store.read() 获取全部数据自己算

## 前端公共模块（P1 提供）
- api-client.js: apiRequest()
- session-ui.js: checkSession(), renderNav()
- form-utils.js: 表单反馈工具（如果有的话）

## 参考
- 实施计划 Task 22-26 含完整代码
- 概要设计第六、八、九章
- 参考 enterticketsystem/ 的管理页面风格（admin-management.js, admin-stats.js）

请按顺序完成：schemas → template_service → admin_service → routes → 前端页面。
```

---

## P5：测试 + 集成 + 文档 + 演示

```
我是 5 人团队中的 P5，负责测试、集成验证、文档，以及周五的系统演示讲解。

## 前提
P1 已建好项目骨架和认证模块。P2/P3/P4 正在并行开发各自模块。
我不依赖他们完成——可以先写测试基础设施和认证模块的测试。

我是唯一接触全部模块的人（写了所有模块的测试），所以周五由我来演示系统。

## 我的任务
按照实施计划 Task 27-30：

### 测试基础设施
1. tests/conftest.py — 测试配置工厂函数（make_settings, make_repo, make_client, seed_xxx, login）
2. tests/test_storage.py — JSON 存储层测试（原子写入、并发读、数据完整性）

### 模块测试（每人完成后我写对应测试）
3. tests/test_auth_routes.py — 登录/注册/退出/me，402/403 场景
4. tests/test_contract_routes.py — 合同 CRUD + 状态流转全部路径
5. tests/test_internal_routes.py — 审批通过/驳回/越级/消息/到期提醒
6. tests/test_template_routes.py — 模板 CRUD + 启停
7. tests/test_admin_routes.py — 用户管理 + 统计看板

### 文档
8. 完善需求分析文档
9. 完善系统设计文档（架构图、分层说明、状态机）
10. 测试报告（用例清单 + 执行结果）
11. 汇报 PPT（项目概述 → 核心技术 → 功能演示 → 团队分工 → 总结）

### 集成（Day2 下午）
12. 协助 P1 做端到端验证流程
13. 运行全部测试并生成报告

### 演示准备（Day2 下午 + 周五上午）
14. 准备演示脚本——按业务流程串联所有页面：
    管理员登录 → 创建模板 → 创建用户（approver1, approver2, handler1）
    → 经办人登录 → 基于模板创建合同 → 提交审批
    → 主管审批人登录 → 审批通过
    → 法务审批人登录 → 审批通过
    → 经办人登录 → 确认签订
    → 管理员登录 → 查看数据看板
15. 提前预制演示数据（四个账号 + 一个走完完整审批链的合同），避免现场翻车
16. 周五演示时我就是主讲人——讲解系统设计思路 + 按业务流程演示全系统

## 测试模式（从 enterticketsystem/ 复用）
```python
import anyio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import get_settings

def test_xxx(tmp_path):
    settings = make_settings(tmp_path)  # 指向临时目录
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            resp = await client.post("/api/v1/auth/login", json={...})
            assert resp.status_code == 200

    anyio.run(run)
```

## 关键
- 每个测试独立创建 app、repo、client，不共享状态
- 数据文件通过 pytest tmp_path fixture 指向临时目录
- 使用 app.dependency_overrides 注入测试配置
- 参考 enterticketsystem/backend/tests/ 的测试风格

## 参考
- 实施计划 Task 27-30 含 conftest 完整代码和测试示例
- 概要设计第十一章（测试策略）
- enterticketsystem/backend/tests/ 的测试模式

请按顺序完成：conftest → storage 测试 → auth 测试 → 合同测试 → 审批测试 → 模板测试 → 管理员测试 → 文档。
```

---

## 集成者（P1 或指定一人，Day2 下午执行）

```
我是集成者，现在需要把所有模块拼起来。

## 背景
P2 完成了 contracts.py 路由和合同页面
P3 完成了 internal.py 路由和审批/消息页面
P4 完成了 templates.py + admin.py 路由和管理页面
P5 完成了测试套件
P1（我）完成了认证模块和基础设施

现在需要把这些全部整合到一起。

## 我的任务

### 1. 路由注册
在 backend/app/main.py 中确保所有路由已注册：
```python
from app.api.routes import auth, contracts, internal, templates, admin

app.include_router(auth.router)
app.include_router(contracts.router)
app.include_router(internal.router)
app.include_router(templates.router)
app.include_router(admin.router)
```

### 2. 验证启动
```bash
cd backend
source .venv/Scripts/activate
python -m uvicorn app.main:app --reload
```
访问 http://localhost:8000，确认能跳转登录页，无 import 错误。

### 3. 端到端验证
依次验证：
- 管理员登录 → 创建模板 → 创建用户（handler1 + approver1 + approver2）
- 经办人登录 → 基于模板创建合同 → 提交审批
- 主管审批人登录 → 待审批列表 → 通过
- 法务审批人登录 → 待审批列表 → 通过
- 经办人登录 → 合同已通过 → 确认签订
- 管理员登录 → 数据看板正常

### 4. 运行全部测试
```bash
cd backend
pytest -v
```
如有 FAIL，根据错误信息定位并修复。

### 5. 收尾
确认前端所有页面可访问，无 404，无 JS 报错。
```

---

## 快速对照表

| 角色 | 我写哪些文件 | 我不碰哪些文件 |
|------|-------------|---------------|
| P1 | `storage/`, `security/`, `domain/`, `repositories/`, `api/dependencies.py`, `api/errors.py`, `api/routes/auth.py`, `services/auth_service.py`, `schemas/auth.py`, `schemas/users.py`, `main.py`, `config.py`, `bootstrap.py`, `pages/public/`, `assets/js/api-client.js`, `assets/js/session-ui.js`, `assets/css/style.css` | P2/P3/P4 的路由和服务文件 |
| P2 | `schemas/contracts.py`, `services/contract_service.py`, `api/routes/contracts.py`, `pages/handler/`, `assets/js/handler.js` | P1/P3/P4 的文件 |
| P3 | `schemas/messages.py`, `services/approval_service.py`, `services/message_service.py`, `api/routes/internal.py`, `pages/internal/`, `assets/js/internal.js` | P1/P2/P4 的文件 |
| P4 | `schemas/templates.py`, `services/template_service.py`, `services/admin_service.py`, `api/routes/templates.py`, `api/routes/admin.py`, `pages/admin/`, `assets/js/admin.js` | P1/P2/P3 的文件 |
| P5 | `tests/` 全部, `docs/` 全部 | 所有业务代码 |
