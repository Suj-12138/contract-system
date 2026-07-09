# Git 协作操作指南

> 适用团队：5 人 | 仓库所有者：P1 | 工具：Git + GitHub

---

## 一、P1 初始化（仓库所有者）

### 1. 在 GitHub 上创建仓库

1. 打开 https://github.com ，登录你的账号
2. 右上角 `+` → `New repository`
3. Repository name：`contract-system`
4. **不要勾选** "Add a README file" 和 "Add .gitignore"（项目里已经有了）
5. 点击 `Create repository`
6. 记下仓库地址：`https://github.com/Suj-12138/contract-system.git`

### 2. 本地项目推送到 GitHub

在 VS Code 终端中进入项目文件夹：

```bash
cd contract-system

# 初始化 Git
git init

# 添加全部文件并首次提交
git add -A
git commit -m "init: 项目基线文档 — 需求分析 + 概要设计 + 实施计划"

# 关联 GitHub 仓库
git remote add origin https://github.com/Suj-12138/contract-system.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

推送成功后，刷新 GitHub 页面，应该看到 5 份基线文档。

### 3. 创建你自己的开发分支

```bash
git checkout -b feature/auth-infra
```

在这条分支上完成 Task 1-12（项目骨架 + 认证模块）。做完后：

```bash
git add -A
git commit -m "feat: 项目骨架 — FastAPI + JSON存储 + 认证模块"
git push -u origin feature/auth-infra
```

---

## 二、组员克隆与分支（P2/P3/P4/P5）

### 1. 克隆仓库

```bash
git clone https://github.com/Suj-12138/contract-system.git
cd contract-system
```

### 2. 拉取 P1 的骨架

```bash
git fetch origin
git checkout feature/auth-infra     # 先看看骨架有没有问题
cd backend
python -m venv .venv
source .venv/Scripts/activate       # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

然后创建 `.env` 配置文件（`.gitignore` 已排除，每人自己创建）：

```bash
cp .env.example .env
```

或手动创建 `backend/.env`，内容：
```
APP_NAME=企业合同管理系统
APP_ENV=local
SESSION_COOKIE_NAME=contract_session
SESSION_COOKIE_SECURE=false
SESSION_TTL_HOURS=8
EXPIRY_WARN_DAYS=30
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_EMAIL=admin@contract-system.local
INITIAL_ADMIN_PASSWORD=admin123456
```

### 3. 创建自己的开发分支

```bash
# 回到 main，基于 main 建自己的分支
git checkout main

# P2 执行：
git checkout -b feature/contracts

# P3 执行：
git checkout -b feature/approval-msg

# P4 执行：
git checkout -b feature/templates-admin

# P5 执行：
git checkout -b feature/tests-docs
```

### 4. 日常开发

在自己的分支上写代码，每完成一个功能点就提交：

```bash
git add -A
git commit -m "feat: 合同 Schema + Service + 路由"
# 继续写下一个...
git add -A
git commit -m "feat: 合同列表页面 + 详情页面"
```

**不要直接改 main 分支，不要 merge main 到自己的分支。** 只在各自的分支上工作。

### 5. 推送自己的分支到 GitHub

```bash
git push -u origin feature/contracts     # P2 执行
git push -u origin feature/approval-msg  # P3 执行
git push -u origin feature/templates-admin # P4 执行
git push -u origin feature/tests-docs    # P5 执行
```

---

## 三、P1 合并（Day2 下午）

所有分支推送后，P1 逐个合并到 main。

### 1. 确保本地代码最新

```bash
git checkout main
git pull origin main
```

### 2. 逐个合并

```bash
# 先合并你自己的
git merge feature/auth-infra

# 合并 P2
git merge feature/contracts

# 合并 P3
git merge feature/approval-msg

# 合并 P4
git merge feature/templates-admin

# 合并 P5
git merge feature/tests-docs
```

### 3. 每次合并后验证

```bash
# 每次合并完，启动服务器看看能不能跑
cd backend
source .venv/Scripts/activate
python -m uvicorn app.main:app --reload
# 访问 http://localhost:8000 ，确认没有报错
```

如果某个分支合并时提示冲突（CONFLICT），告诉那个人一起看冲突在哪，解决后继续。

### 4. 最终验证

```bash
# 运行全部测试
cd backend
pytest -v
```

### 5. 推送到 GitHub

```bash
git push origin main
```

---

## 四、常见问题

### Q: 合并冲突怎么办？

**极少发生**——因为每人只写自己目录下的文件，文件不重叠。唯一可能冲突的是：

| 文件 | 解决方式 |
|------|----------|
| `app/main.py` | P1 已预留所有路由注册注释，其他人不碰这个文件 |
| `app/domain/enums.py` | 接受双方更改（一个加了角色枚举，一个加了状态枚举，不冲突） |
| `assets/css/style.css` | 接受双方更改（各自追加在末尾） |

如果提示冲突，先看是哪个文件，把两人的改动都保留（一行都不能丢），然后：

```bash
git add 冲突的文件
git commit -m "merge: 解决 xxx 冲突"
```

### Q: 不小心改错了别人的文件怎么办？

```bash
# 放弃对这个文件的修改，恢复原样
git checkout -- 文件路径
```

### Q: 提交信息写错了怎么办？

```bash
git commit --amend -m "正确的内容"
```

### Q: 忘记推送了，回家后怎么继续？

没办法——Git 是本地仓库，没 push 的代码只在你电脑上。**养成习惯：每天结束前 push 一次。**

### Q: 有人 push 后我 pull 不下来？

```bash
# 先暂存自己的改动
git stash
# 拉取
git pull
# 恢复改动
git stash pop
```

### Q: 完全搞砸了，想重来？

最坏情况：删掉本地文件夹，重新 clone。**前提是你每次 push 了。**

---

## 五、命令速查表

| 操作 | 命令 |
|------|------|
| 查看当前状态 | `git status` |
| 添加所有改动 | `git add -A` |
| 提交 | `git commit -m "本次改了什么"` |
| 推送到 GitHub | `git push` |
| 拉取最新代码 | `git pull` |
| 查看所有分支 | `git branch -a` |
| 切换分支 | `git checkout 分支名` |
| 创建并切换新分支 | `git checkout -b 新分支名` |
| 查看提交历史 | `git log --oneline` |
| 放弃某个文件的改动 | `git checkout -- 文件路径` |
| 暂存当前改动 | `git stash` |
| 恢复暂存 | `git stash pop` |
