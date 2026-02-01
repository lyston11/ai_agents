# AI Agents 学习项目

这是一个 AI Agents 相关的学习项目。

## 项目结构

```
ai-agents/
├── main.py                    # 主程序入口
├── week1/                     # 第一周学习内容
│   └── async_request_demo.py  # 装饰器示例
├── git-sync.sh                # Git 同步脚本
└── README.md                  # 项目说明
```

## 使用说明

1. 安装 Python 3.x
2. 运行主程序：
   ```bash
   python main.py
   ```

## Git 同步使用指南

项目提供了便捷的 Git 同步脚本 `git-sync.sh`，方便在不同电脑间同步代码。

### 首次使用（在当前电脑）

```bash
# 初始化并推送到 GitHub
./git-sync.sh init
```

### 在新电脑上使用

```bash
# 1. 克隆项目
git clone git@github.com:lyston11/ai_agents.git

# 2. 进入项目目录
cd ai_agents

# 3. 设置脚本执行权限
chmod +x git-sync.sh

# 4. 开始使用
./git-sync.sh sync
```

### 日常使用命令

```bash
# 保存并推送当前更改
./git-sync.sh push

# 从 GitHub 拉取最新更改
./git-sync.sh pull

# 智能同步（先拉取，再推送）- 推荐！
./git-sync.sh sync

# 查看当前文件状态
./git-sync.sh status

# 显示帮助信息
./git-sync.sh help
```

### 典型工作流程

**在电脑 A 上工作后：**
```bash
./git-sync.sh push
```

**切换到电脑 B 前：**
```bash
./git-sync.sh pull
```

**不确定状态时：**
```bash
./git-sync.sh sync  # 自动处理拉取和推送
```

## 学习进度

- [x] Week 1: Python 装饰器基础
- [ ] 待继续...
