"""
tools.bash - Bash 命令执行工具
Inspired by claw-code's BashTool
"""
from __future__ import annotations
import asyncio
import time
from .base import Tool, ToolResult, ToolCategory


class BashTool(Tool):
    """Execute Shell commands"""
    name = "bash"
    description = "Execute a bash command. Use for running scripts, git, npm, python, etc."
    category = ToolCategory.EXECUTION
    
    parameters = [
        {"name": "command", "description": "The bash command to execute", "type": "string", "required": True},
        {"name": "timeout", "description": "Timeout in seconds (default 30)", "type": "integer", "required": False},
        {"name": "working_dir", "description": "Working directory for the command", "type": "string", "required": False},
    ]
    
    MAX_TIMEOUT = 300
    
    async def execute(self, command: str, timeout: int = 30, working_dir: str = None, **kwargs) -> ToolResult:
        start_time = time.time()
        
        # 安全检查
        dangerous = ["rm -rf /", ":(){ :|:& };:", "> /dev/sda", "mkfs"]
        for d in dangerous:
            if d in command:
                return ToolResult(success=False, error=f"Blocked dangerous command: {d}", tool_name=self.name, duration=time.time() - start_time)
        
        timeout = min(timeout or 30, self.MAX_TIMEOUT)
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(success=False, error=f"Command timed out after {timeout}s", tool_name=self.name, duration=time.time() - start_time)
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            duration = time.time() - start_time
            
            if process.returncode == 0:
                return ToolResult(success=True, output=stdout_str or "(no output)", tool_name=self.name, duration=duration, metadata={"returncode": 0})
            else:
                return ToolResult(success=False, output=stdout_str or "", error=stderr_str or f"Exit code: {process.returncode}", tool_name=self.name, duration=duration, metadata={"returncode": process.returncode})
                
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name, duration=time.time() - start_time)
