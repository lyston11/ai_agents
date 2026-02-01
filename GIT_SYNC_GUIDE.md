# Git 同步脚本使用指南

## 📋 目录

- [快速开始](#快速开始)
- [命令说明](#命令说明)
- [使用场景](#使用场景)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 在当前电脑（已初始化）

项目已经初始化完成，直接使用即可：

```bash
# 查看帮助
./git-sync.sh help

# 智能同步（推荐）
./git-sync.sh sync
```

### 在新电脑上使用

```bash
# 1. 克隆项目
git clone git@github.com:lyston11/ai_agents.git

# 2. 进入项目目录
cd ai_agents

# 3. 给脚本执行权限
chmod +x git-sync.sh

# 4. 开始使用
./git-sync.sh sync
```

---

## 📖 命令说明

### `./git-sync.sh init`

**功能**：初始化仓库并首次推送到 GitHub

**使用场景**：只在第一次创建项目时使用

**示例**：
```bash
./git-sync.sh init
```

**说明**：本项目已经初始化完成，你通常不需要使用这个命令

---

### `./git-sync.sh push`

**功能**：保存并推送当前更改到 GitHub

**使用场景**：当你完成工作，想把代码上传到 GitHub

**示例**：
```bash
./git-sync.sh push
```

**交互流程**：
1. 显示当前有哪些文件被修改
2. 提示你输入提交信息（可直接回车使用默认信息）
3. 自动提交并推送到 GitHub

**示例输出**：
```
📤 推送更改到 GitHub...
📋 当前更改:
 M week1/async_request_demo.py
 A week2/new_file.py
💬 请输入提交信息（直接回车使用默认信息）:
```

---

### `./git-sync.sh pull`

**功能**：从 GitHub 拉取最新更改

**使用场景**：换到另一台电脑时，拉取最新代码

**示例**：
```bash
./git-sync.sh pull
```

**说明**：
- 如果有本地未提交的更改，会自动保存（stash）
- 拉取完成后，会自动恢复本地更改

---

### `./git-sync.sh status`

**功能**：查看当前文件状态

**使用场景**：想知道哪些文件被修改了

**示例**：
```bash
./git-sync.sh status
```

**示例输出**：
```
📊 当前状态:
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  modified:   week1/async_request_demo.py

Untracked files:
  week2/new_file.py
```

---

### `./git-sync.sh sync` ⭐️ 推荐

**功能**：智能同步（先拉取，再推送）

**使用场景**：
- 不确定本地和远程哪个是最新的
- 想一次性完成所有同步操作
- **日常使用最推荐！**

**示例**：
```bash
./git-sync.sh sync
```

**工作流程**：
1. 从 GitHub 拉取最新代码
2. 如果有本地更改，自动推送到 GitHub
3. 如果没有更改，提示已是最新状态

---

### `./git-sync.sh clone`

**功能**：显示如何在新电脑上克隆项目

**使用场景**：想在新电脑上获取项目

**示例**：
```bash
./git-sync.sh clone
```

**示例输出**：
```
📦 克隆项目...
这个命令用于在新电脑上克隆项目

请在新电脑上运行以下命令:
git clone git@github.com:lyston11/ai_agents.git

克隆后，将此脚本复制到项目目录，即可使用！
```

---

### `./git-sync.sh help`

**功能**：显示帮助信息

**示例**：
```bash
./git-sync.sh help
```

---

## 💼 使用场景

### 场景 1：在公司完成工作

```bash
# 保存并推送代码
./git-sync.sh push

# 输入提交信息
完成 Week 1 学习内容
```

**或者使用智能同步：**
```bash
./git-sync.sh sync
```

---

### 场景 2：回家后继续工作

```bash
# 拉取最新代码
./git-sync.sh pull

# 或者直接使用智能同步
./git-sync.sh sync
```

---

### 场景 3：在公司和家里来回切换

**推荐使用智能同步，一个命令搞定一切：**

```bash
# 每次开始工作前
./git-sync.sh sync

# 工作完成后
./git-sync.sh sync
```

---

### 场景 4：想查看有什么改动

```bash
# 查看状态
./git-sync.sh status
```

---

### 场景 5：新买了一台电脑

```bash
# 1. 先配置 SSH 密钥（如果还没有）
ssh-keygen -t rsa -C "your_email@example.com"

# 2. 复制公钥到 GitHub
cat ~/.ssh/id_rsa.pub | pbcopy
# 然后访问 https://github.com/settings/keys 添加

# 3. 克隆项目
git clone git@github.com:lyston11/ai_agents.git

# 4. 进入项目
cd ai_agents

# 5. 设置脚本权限
chmod +x git-sync.sh

# 6. 开始使用
./git-sync.sh sync
```

---

## ❓ 常见问题

### Q1: 直接用 `./git-sync.sh` 不带命令会怎样？

**A**: 会显示帮助信息，等同于 `./git-sync.sh help`

---

### Q2: 我应该用 push/pull 还是 sync？

**A**: 
- **日常使用推荐 `sync`**：自动处理拉取和推送，更智能
- **明确只想推送**：用 `push`
- **明确只想拉取**：用 `pull`

大多数情况下，**`sync` 是最好的选择**。

---

### Q3: 提交信息可以用中文吗？

**A**: 可以！完全支持中文提交信息。

```bash
./git-sync.sh push
# 输入：完成装饰器学习
```

---

### Q4: 如果 push 时忘记输入提交信息会怎样？

**A**: 直接回车会使用默认信息（带时间戳），例如：

```
更新: 2026-02-01 15:30:45
```

---

### Q5: 多台电脑都要配置 SSH 密钥吗？

**A**: 是的。每台电脑都需要：
1. 生成 SSH 密钥
2. 把公钥添加到 GitHub
3. 测试连接：`ssh -T git@github.com`

---

### Q6: 脚本执行失败怎么办？

**A**: 检查以下几点：
1. 是否有执行权限：`ls -la git-sync.sh`
2. 如果没有，运行：`chmod +x git-sync.sh`
3. 确认 SSH 连接正常：`ssh -T git@github.com`

---

### Q7: 可以直接用 git 命令吗？

**A**: 当然可以！这个脚本只是为了方便，你依然可以使用原生 git 命令：

```bash
git add .
git commit -m "提交信息"
git push

git pull
```

---

### Q8: 如何查看远程仓库地址？

**A**: 运行以下命令：

```bash
git remote -v
```

应该显示：
```
origin  git@github.com:lyston11/ai_agents.git (fetch)
origin  git@github.com:lyston11/ai_agents.git (push)
```

---

## 🎯 最佳实践

### 推荐工作流程

```bash
# 1. 开始工作前
./git-sync.sh sync          # 拉取最新代码

# 2. 进行编码工作
# ... 写代码 ...

# 3. 随时查看状态
./git-sync.sh status        # 查看改动

# 4. 工作结束
./git-sync.sh sync          # 推送更改
```

---

## 📞 需要帮助？

如果遇到问题：

1. 查看帮助：`./git-sync.sh help`
2. 查看状态：`./git-sync.sh status`
3. 测试 GitHub 连接：`ssh -T git@github.com`

---

## 🔗 相关链接

- GitHub 仓库：https://github.com/lyston11/ai_agents
- SSH 密钥设置：https://github.com/settings/keys
- Git 官方文档：https://git-scm.com/doc

---

**最后提醒**：日常使用，记住这一个命令就够了！

```bash
./git-sync.sh sync
```

简单、快速、不会出错！✨
