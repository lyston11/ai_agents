#!/bin/bash

# Git 同步脚本 - 用于在不同电脑间同步项目
# 使用方法: ./git-sync.sh [命令]

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# GitHub 仓库信息
REPO_URL="git@github.com:lyston11/ai_agents.git"
BRANCH="main"

# 显示使用说明
show_help() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}     Git 项目同步脚本${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
    echo "使用方法: ./git-sync.sh [命令]"
    echo ""
    echo "命令列表:"
    echo -e "  ${GREEN}init${NC}       - 初始化仓库并首次推送到 GitHub"
    echo -e "  ${GREEN}push${NC}       - 保存并推送当前更改到 GitHub"
    echo -e "  ${GREEN}pull${NC}       - 从 GitHub 拉取最新更改"
    echo -e "  ${GREEN}status${NC}     - 查看当前文件状态"
    echo -e "  ${GREEN}sync${NC}       - 智能同步（先拉取，再推送）"
    echo -e "  ${GREEN}clone${NC}      - 在新电脑上克隆项目"
    echo -e "  ${GREEN}help${NC}       - 显示此帮助信息"
    echo ""
}

# 初始化并首次推送
init_repo() {
    echo -e "${BLUE}🚀 初始化 Git 仓库...${NC}"
    
    # 检查是否已经是 Git 仓库
    if [ -d .git ]; then
        echo -e "${YELLOW}⚠️  已经是 Git 仓库${NC}"
    else
        git init
        echo -e "${GREEN}✅ Git 仓库初始化完成${NC}"
    fi
    
    # 配置用户信息（如果还没配置）
    if [ -z "$(git config user.name)" ]; then
        echo -e "${YELLOW}📝 请输入你的 Git 用户名:${NC}"
        read username
        git config --global user.name "$username"
    fi
    
    if [ -z "$(git config user.email)" ]; then
        echo -e "${YELLOW}📝 请输入你的 Git 邮箱:${NC}"
        read email
        git config --global user.email "$email"
    fi
    
    # 添加所有文件
    echo -e "${BLUE}📦 添加文件...${NC}"
    git add .
    
    # 提交
    echo -e "${BLUE}💾 提交更改...${NC}"
    git commit -m "Initial commit: 初始化项目"
    
    # 设置远程仓库
    if ! git remote | grep -q origin; then
        echo -e "${BLUE}🔗 添加远程仓库...${NC}"
        git remote add origin $REPO_URL
    fi
    
    # 推送到 GitHub
    echo -e "${BLUE}⬆️  推送到 GitHub...${NC}"
    git branch -M $BRANCH
    git push -u origin $BRANCH
    
    echo -e "${GREEN}✅ 初始化完成！项目已推送到 GitHub${NC}"
}

# 推送更改
push_changes() {
    echo -e "${BLUE}📤 推送更改到 GitHub...${NC}"
    
    # 检查是否有更改
    if [ -z "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}⚠️  没有需要提交的更改${NC}"
        return
    fi
    
    # 显示更改
    echo -e "${BLUE}📋 当前更改:${NC}"
    git status --short
    
    # 添加所有更改
    git add .
    
    # 获取提交信息
    echo -e "${YELLOW}💬 请输入提交信息（直接回车使用默认信息）:${NC}"
    read commit_msg
    
    if [ -z "$commit_msg" ]; then
        commit_msg="更新: $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    # 提交
    git commit -m "$commit_msg"
    
    # 推送
    git push origin $BRANCH
    
    echo -e "${GREEN}✅ 推送完成！${NC}"
}

# 拉取更新
pull_changes() {
    echo -e "${BLUE}📥 从 GitHub 拉取最新更改...${NC}"
    
    # 检查是否有本地更改
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}⚠️  检测到本地更改，先保存当前工作...${NC}"
        git stash
        has_stash=true
    fi
    
    # 拉取
    git pull origin $BRANCH
    
    # 恢复保存的更改
    if [ "$has_stash" = true ]; then
        echo -e "${BLUE}📦 恢复本地更改...${NC}"
        git stash pop
    fi
    
    echo -e "${GREEN}✅ 拉取完成！${NC}"
}

# 查看状态
show_status() {
    echo -e "${BLUE}📊 当前状态:${NC}"
    git status
}

# 智能同步
smart_sync() {
    echo -e "${BLUE}🔄 开始智能同步...${NC}"
    
    # 先拉取
    pull_changes
    
    echo ""
    
    # 再推送
    if [ -n "$(git status --porcelain)" ]; then
        push_changes
    else
        echo -e "${GREEN}✅ 已是最新状态，无需推送${NC}"
    fi
}

# 克隆项目（在新电脑上使用）
clone_repo() {
    echo -e "${BLUE}📦 克隆项目...${NC}"
    echo -e "${YELLOW}这个命令用于在新电脑上克隆项目${NC}"
    echo ""
    echo "请在新电脑上运行以下命令:"
    echo -e "${GREEN}git clone $REPO_URL${NC}"
    echo ""
    echo "克隆后，将此脚本复制到项目目录，即可使用！"
}

# 主逻辑
case "$1" in
    init)
        init_repo
        ;;
    push)
        push_changes
        ;;
    pull)
        pull_changes
        ;;
    status)
        show_status
        ;;
    sync)
        smart_sync
        ;;
    clone)
        clone_repo
        ;;
    help|"")
        show_help
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
