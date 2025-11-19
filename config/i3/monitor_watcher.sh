#!/bin/bash
# 初始状态记录
PREV_STATE=$(xrandr --query | grep -w connected)

while true; do
    # 获取当前状态
    CURRENT_STATE=$(xrandr --query | grep -w connected)
    
    # 检测状态变化
    if [ "$PREV_STATE" != "$CURRENT_STATE" ]; then
        echo "[$(date)] 显示器配置变化 detected"
        PREV_STATE="$CURRENT_STATE"
        
        # 执行您的布局调整脚本
        ~/.on_monitor_change
    fi
    
    sleep 2  # 轮询间隔(秒)
done

