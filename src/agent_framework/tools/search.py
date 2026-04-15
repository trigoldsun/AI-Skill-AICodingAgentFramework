"""
tools.search - 搜索工具集
Inspired by claw-code's Grep and Glob tools
"""
from __future__ import annotations
import re
import time
from pathlib import Path
from .base import Tool, ToolResult, ToolCategory


class GrepSearchTool(Tool):
    """正则搜索"""
    name = "grep"
    description = "Search for text patterns in files using regex."
    category = ToolCategory.SEARCH
    
    parameters = [
        {"name": "pattern", "description": "Regex pattern to search for", "type": "string", "required": True},
        {"name": "path", "description": "Directory or file to search in (default: current directory)", "type": "string", "required": False},
        {"name": "file_pattern", "description": "File pattern to match (e.g., '*.py')", "type": "string", "required": False},
        {"name": "case_sensitive", "description": "Case sensitive search", "type": "boolean", "required": False},
        {"name": "max_results", "description": "Maximum number of results", "type": "integer", "required": False},
    ]
    
    async def execute(self, pattern: str, path: str = ".", file_pattern: str = "*", case_sensitive: bool = True, max_results: int = 100, **kwargs) -> ToolResult:
        start_time = time.time()
        try:
            search_path = Path(path).expanduser().resolve()
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
            
            results = []
            for file_path in search_path.rglob(file_pattern):
                if not file_path.is_file():
                    continue
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        for lineno, line in enumerate(f, 1):
                            if regex.search(line):
                                results.append(f"{file_path.relative_to(search_path)}:{lineno}: {line.rstrip()}")
                                if len(results) >= max_results:
                                    break
                except (PermissionError, IsADirectoryError):
                    continue
                if len(results) >= max_results:
                    break
            
            return ToolResult(success=True, output="\n".join(results) if results else "No matches found", tool_name=self.name, duration=time.time() - start_time, metadata={"matches": len(results), "pattern": pattern})
        except re.error as e:
            return ToolResult(success=False, error=f"Invalid regex: {e}", tool_name=self.name, duration=time.time() - start_time)
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name, duration=time.time() - start_time)


class GlobSearchTool(Tool):
    """Glob 文件搜索"""
    name = "glob"
    description = "Find files matching a glob pattern."
    category = ToolCategory.SEARCH
    
    parameters = [
        {"name": "pattern", "description": "Glob pattern (e.g., '**/*.py')", "type": "string", "required": True},
        {"name": "path", "description": "Base directory to search from", "type": "string", "required": False},
        {"name": "max_results", "description": "Maximum number of results", "type": "integer", "required": False},
    ]
    
    async def execute(self, pattern: str, path: str = ".", max_results: int = 100, **kwargs) -> ToolResult:
        start_time = time.time()
        try:
            search_path = Path(path).expanduser().resolve()
            results = list(search_path.glob(pattern))[:max_results]
            
            output = [str(r.relative_to(search_path)) for r in results]
            return ToolResult(success=True, output="\n".join(output) if output else "No files found", tool_name=self.name, duration=time.time() - start_time, metadata={"matches": len(results), "pattern": pattern})
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name, duration=time.time() - start_time)
