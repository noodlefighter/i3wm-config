#!/bin/bash

# 获取脚本所在目录（处理符号链接情况）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 使用 $HOME 而不是 ~，确保路径正确展开
MONITOR_DEFINE="$HOME/.monitor_define"

if [[ ! -f "${MONITOR_DEFINE}" ]]; then
    echo "错误: 未找到配置文件 ${MONITOR_DEFINE}"
    exit 1
fi

echo "加载配置: ${MONITOR_DEFINE}"
source "${MONITOR_DEFINE}"

if [[ -z "${LEFT}" || -z "${RIGHT}" ]]; then
    echo "错误: 环境变量 LEFT 或 RIGHT 未设置"
    exit 1
fi

# 检查 python3 是否存在
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查 workspace_monitor.py 是否存在
if [[ ! -f "${SCRIPT_DIR}/workspace_monitor.py" ]]; then
    echo "错误: 未找到 workspace_monitor.py"
    exit 1
fi

# 检查是否已有实例在运行
PID_FILE="/tmp/workspace_monitor.pid"
if [[ -f "${PID_FILE}" ]]; then
    OLD_PID=$(cat "${PID_FILE}")
    if kill -0 "${OLD_PID}" 2>/dev/null; then
        echo "工作区监控器已在运行 (PID: ${OLD_PID})"
        exit 0
    else
        rm -f "${PID_FILE}"
    fi
fi

# 启动工作区监控器
cd "${SCRIPT_DIR}"
nohup python3 workspace_monitor.py "${LEFT}" "${RIGHT}" > /tmp/workspace_monitor.log 2>&1 &
NEW_PID=$!
echo "${NEW_PID}" > "${PID_FILE}"
echo "工作区监控器已启动 (PID: ${NEW_PID})"
echo "日志文件: /tmp/workspace_monitor.log"

