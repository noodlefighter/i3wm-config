#!/usr/bin/env python3
"""
工作区监控脚本 - 自动将工作区移动到正确的屏幕

使用方法:
    python3 workspace_monitor.py <左屏幕名字> <右屏幕名字>

示例:
    python3 workspace_monitor.py DVI-D-0 HDMI-0

功能:
    1. 定期检查所有工作区的位置
    2. 根据预定义规则将工作区移动到正确的屏幕
    3. 支持自定义工作区分配规则
"""

import subprocess
import json
import time
import argparse
import sys
import signal
from typing import Dict, List, Tuple


class WorkspaceMonitor:
    """工作区监控器"""
    
    def __init__(self, left_output: str, right_output: str, 
                 left_workspaces: List[int] = None, 
                 right_workspaces: List[int] = None,
                 check_interval: float = 2.0):
        """
        初始化监控器
        
        Args:
            left_output: 左屏幕名称
            right_output: 右屏幕名称
            left_workspaces: 应该在左屏幕的工作区列表（默认: [0, 6, 7, 8, 9]）
            right_workspaces: 应该在右屏幕的工作区列表（默认: [1, 2, 3, 4, 5]）
            check_interval: 检查间隔（秒）
        """
        self.left_output = left_output
        self.right_output = right_output
        
        if left_workspaces is None:
            self.left_workspaces = [0, 6, 7, 8, 9, 10]
        else:
            self.left_workspaces = left_workspaces
            
        if right_workspaces is None:
            self.right_workspaces = [1, 2, 3, 4, 5]
        else:
            self.right_workspaces = right_workspaces
            
        self.check_interval = check_interval
        self.running = True
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """处理退出信号"""
        print("\n收到退出信号，正在停止监控...")
        self.running = False
    
    def _get_active_outputs(self) -> List[str]:
        """
        获取当前活动的显示器列表
        
        Returns:
            活动显示器名称列表
        """
        try:
            result = subprocess.run(
                ['i3-msg', '-t', 'get_outputs'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return []
            
            outputs = json.loads(result.stdout)
            return [o['name'] for o in outputs if o.get('active', False)]
            
        except Exception:
            return []
    
    def _run_i3_command(self, command: str, debug: bool = False) -> bool:
        """
        执行i3-msg命令
        
        Args:
            command: 要执行的命令
            debug: 是否打印调试信息
            
        Returns:
            命令是否成功
        """
        try:
            if debug:
                print(f"执行命令: i3-msg '{command}'")
            
            result = subprocess.run(
                ['i3-msg', command],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if debug:
                print(f"返回码: {result.returncode}")
                print(f"标准输出: {result.stdout}")
                print(f"错误输出: {result.stderr}")
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                print(f"命令返回错误码: {result.returncode}, 错误信息: {error_msg}")
                return False
            
            try:
                response = json.loads(result.stdout)
                if debug:
                    print(f"解析的响应: {response}")
                
                if isinstance(response, list) and len(response) > 0:
                    success = response[0].get('success', False)
                    if not success and 'error' in response[0]:
                        print(f"i3 命令错误: {response[0]['error']}")
                    if debug:
                        print(f"命令成功: {success}")
                    return success
                return False
            except json.JSONDecodeError:
                if result.stderr:
                    print(f"命令错误输出: {result.stderr}")
                    return False
                return True
                
        except subprocess.TimeoutExpired:
            print(f"命令超时: {command}")
            return False
        except Exception as e:
            print(f"执行命令失败: {e}")
            return False
    
    def _get_workspaces(self) -> List[Dict]:
        """
        获取所有工作区信息
        
        Returns:
            工作区信息列表
        """
        try:
            result = subprocess.run(
                ['i3-msg', '-t', 'get_workspaces'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                print(f"获取工作区信息失败: {result.stderr}")
                return []
            
            workspaces = json.loads(result.stdout)
            return workspaces
            
        except subprocess.TimeoutExpired:
            print("获取工作区信息超时")
            return []
        except json.JSONDecodeError as e:
            print(f"解析工作区信息失败: {e}")
            return []
        except Exception as e:
            print(f"获取工作区信息时出错: {e}")
            return []
    
    def _get_expected_output(self, workspace_num: int) -> str:
        """
        获取工作区应该在的屏幕
        
        Args:
            workspace_num: 工作区编号
            
        Returns:
            屏幕名称
        """
        if workspace_num in self.left_workspaces:
            return self.left_output
        elif workspace_num in self.right_workspaces:
            return self.right_output
        else:
            # 未知工作区，不移动
            return None
    
    def _move_workspace(self, workspace_num: int, target_output: str, debug: bool = False) -> bool:
        """
        移动工作区到指定屏幕
        
        Args:
            workspace_num: 工作区编号
            target_output: 目标屏幕
            debug: 是否打印调试信息
            
        Returns:
            是否移动成功
        """
        # 检查目标显示器是否在线
        active_outputs = self._get_active_outputs()
        if target_output not in active_outputs:
            if debug:
                print(f"目标显示器 {target_output} 不在线，跳过移动")
            return False
        
        workspaces = self._get_workspaces()
        workspace_info = None
        for ws in workspaces:
            if ws.get('num') == workspace_num:
                workspace_info = ws
                break
        
        if not workspace_info:
            if debug:
                print(f"工作区 {workspace_num} 不存在，跳过移动")
            return False
        
        current_output = workspace_info.get('output')
        workspace_name = workspace_info.get('name', str(workspace_num))
        
        if current_output == target_output:
            if debug:
                print(f"工作区 {workspace_num} 已经在 {target_output} 上，无需移动")
            return True
        
        # 使用工作区的完整名称来确保正确匹配（处理有别名的工作区如 "8 toy"）
        command = f'workspace "{workspace_name}"; move workspace to output {target_output}'
        success = self._run_i3_command(command, debug=debug)
        
        if success:
            print(f"已移动工作区 {workspace_num} ({workspace_name}) 到 {target_output}")
        else:
            print(f"移动工作区 {workspace_num} ({workspace_name}) 到 {target_output} 失败")
        
        return success
    
    def check_and_fix_workspaces(self, debug: bool = False) -> int:
        """
        检查并修复工作区位置
        
        Args:
            debug: 是否打印调试信息
            
        Returns:
            修复的工作区数量
        """
        workspaces = self._get_workspaces()
        if not workspaces:
            return 0
        
        fixed_count = 0
        
        for ws in workspaces:
            ws_num = ws.get('num')
            current_output = ws.get('output')
            
            if ws_num is None or current_output is None:
                continue
            
            expected_output = self._get_expected_output(ws_num)
            
            # 跳过未知工作区（不在配置中的工作区）
            if expected_output is None:
                continue
            
            if current_output != expected_output:
                if debug:
                    print(f"工作区 {ws_num} 当前在 {current_output}，应该在 {expected_output}")
                if self._move_workspace(ws_num, expected_output, debug=debug):
                    fixed_count += 1
        
        return fixed_count
    
    def run(self, debug: bool = False):
        """
        运行监控器
        
        Args:
            debug: 是否打印调试信息
        """
        import os
        
        # 检查必要的环境变量
        if not os.environ.get('I3SOCK'):
            print("警告: 未设置 I3SOCK 环境变量，i3-msg 可能无法正常工作")
            print("请确保在 i3 会话中运行此脚本")
        
        if not os.environ.get('DISPLAY'):
            print("警告: 未设置 DISPLAY 环境变量，i3-msg 可能无法正常工作")
        
        print(f"启动工作区监控器")
        print(f"左屏幕: {self.left_output} (工作区: {self.left_workspaces})")
        print(f"右屏幕: {self.right_output} (工作区: {self.right_workspaces})")
        print(f"检查间隔: {self.check_interval} 秒")
        print("按 Ctrl+C 停止监控\n")
        
        # 首次检查
        fixed = self.check_and_fix_workspaces(debug=debug)
        print(f"首次检查修复了 {fixed} 个工作区\n")
        
        # 持续监控
        while self.running:
            try:
                time.sleep(self.check_interval)
                fixed = self.check_and_fix_workspaces(debug=debug)
                
                # 只在有修复时输出信息
                if fixed > 0:
                    print(f"本轮修复了 {fixed} 个工作区")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"监控过程中出错: {e}")
                time.sleep(1)
        
        print("监控已停止")


def parse_workspace_list(workspace_str: str) -> List[int]:
    """
    解析工作区列表字符串
    
    支持格式:
        "1,2,3" -> [1, 2, 3]
        "1-5" -> [1, 2, 3, 4, 5]
        "0,6-9" -> [0, 6, 7, 8, 9]
    """
    workspaces = []
    
    for part in workspace_str.split(','):
        part = part.strip()
        
        if '-' in part:
            start, end = part.split('-', 1)
            start, end = int(start), int(end)
            workspaces.extend(range(start, end + 1))
        else:
            workspaces.append(int(part))
    
    return sorted(set(workspaces))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='工作区监控脚本 - 自动将工作区移动到正确的屏幕',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s DVI-D-0 HDMI-0
  %(prog)s DVI-D-0 HDMI-0 --left-workspaces "0,6-9" --right-workspaces "1-5"
  %(prog)s DVI-D-0 HDMI-0 --interval 1
        '''
    )
    
    parser.add_argument(
        'left_output',
        help='左屏幕名称（使用 xrandr 查看）'
    )
    
    parser.add_argument(
        'right_output',
        help='右屏幕名称（使用 xrandr 查看）'
    )
    
    parser.add_argument(
        '--left-workspaces', '-l',
        help='应该在左屏幕的工作区列表（默认: 0,6-9）',
        default=None
    )
    
    parser.add_argument(
        '--right-workspaces', '-r',
        help='应该在右屏幕的工作区列表（默认: 1-5）',
        default=None
    )
    
    parser.add_argument(
        '--interval', '-i',
        help='检查间隔秒数（默认: 2.0）',
        type=float,
        default=2.0
    )
    
    parser.add_argument(
        '--debug', '-d',
        help='启用调试模式',
        action='store_true',
        default=False
    )
    
    args = parser.parse_args()
    
    left_workspaces = None
    right_workspaces = None
    
    if args.left_workspaces:
        try:
            left_workspaces = parse_workspace_list(args.left_workspaces)
        except ValueError as e:
            print(f"错误: 无效的左工作区列表 '{args.left_workspaces}': {e}")
            sys.exit(1)
    
    if args.right_workspaces:
        try:
            right_workspaces = parse_workspace_list(args.right_workspaces)
        except ValueError as e:
            print(f"错误: 无效的右工作区列表 '{args.right_workspaces}': {e}")
            sys.exit(1)
    
    monitor = WorkspaceMonitor(
        left_output=args.left_output,
        right_output=args.right_output,
        left_workspaces=left_workspaces,
        right_workspaces=right_workspaces,
        check_interval=args.interval
    )
    
    monitor.run(debug=args.debug)


if __name__ == '__main__':
    main()
