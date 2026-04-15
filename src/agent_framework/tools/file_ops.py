"""
tools.file_ops - 文件操作工具集
Inspired by claw-code's Read/Write/Edit tools
"""
from __future__ import annotations
import time
from pathlib import Path
from .base import Tool, ToolResult, ToolCategory


class ReadFileTool(Tool):
    """读取文件内容"""
    name = "read"
    description = "Read the contents of a file. Supports line offsets and limits."
    category = ToolCategory.FILE
    
    parameters = [
        {"name": "path", "description": "Path to the file to read", "type": "string", "required": True},
        {"name": "offset", "description": "Line number to start reading from (1-indexed)", "type": "integer", "required": False},
        {"name": "limit", "description": "Maximum number of lines to read", "type": "integer", "required": False},
    ]
    
    async def execute(self, path: str, offset: int = 0, limit: int = None, **kwargs) -> ToolResult:
        start_time = time.time()
        try:
            file_path = Path(path).expanduser().resolve()
            
            if not file_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}", tool_name=self.name, duration=time.time() - start_time)
            if not file_path.is_file():
                return ToolResult(success=False, error=f"Not a file: {path}", tool_name=self.name, duration=time.time() - start_time)
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                if offset > 0:
                    for _ in range(offset - 1):
                        f.readline()
                content = ''.join(f.readline() for _ in range(limit)) if limit else f.read()
            
            return ToolResult(success=True, output=content, tool_name=self.name, duration=time.time() - start_time,
                metadata={"path": str(file_path), "lines": len(content.splitlines())})
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name, duration=time.time() - start_time)


class WriteFileTool(Tool):
    """写入文件"""
    name = "write"
    description = "Write content to a file. Creates parent directories if needed."
    category = ToolCategory.FILE
    
    parameters = [
        {"name": "path", "description": "Path to the file to write", "type": "string", "required": True},
        {"name": "content", "description": "Content to write to the file", "type": "string", "required": True},
        {"name": "append", "description": "Append to existing file instead of overwriting", "type": "boolean", "required": False},
    ]
    
    async def execute(self, path: str, content: str, append: bool = False, **kwargs) -> ToolResult:
        start_time = time.time()
        try:
            file_path = Path(path).expanduser().resolve()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(success=True, output=f"Written {len(content)} bytes to {file_path}", tool_name=self.name,
                duration=time.time() - start_time, metadata={"path": str(file_path), "bytes": len(content.encode('utf-8'))})
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name, duration=time.time() - start_time)


class EditFileTool(Tool):
    """编辑文件（替换）"""
    name = "edit"
    description = "Edit a file by replacing old text with new text."
    category = ToolCategory.FILE
    
    parameters = [
        {"name": "path", "description": "Path to the file to edit", "type": "string", "required": True},
        {"name": "old_text", "description": "The exact text to replace (must be unique)", "type": "string", "required": True},
        {"name": "new_text", "description": "The replacement text", "type": "string", "required": True},
    ]
    
    async def execute(self, path: str, old_text: str, new_text: str, **kwargs) -> ToolResult:
        start_time = time.time()
        try:
            file_path = Path(path).expanduser().resolve()
            
            if not file_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}", tool_name=self.name, duration=time.time() - start_time)
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                original = f.read()
            
            count = original.count(old_text)
            if count == 0:
                return ToolResult(success=False, error="Text not found in file", tool_name=self.name, duration=time.time() - start_time)
            if count > 1:
                return ToolResult(success=False, error=f"Text appears {count} times, need unique match", tool_name=self.name, duration=time.time() - start_time)
            
            new_content = original.replace(old_text, new_text, 1)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return ToolResult(success=True, output=f"Edited {file_path}", tool_name=self.name, duration=time.time() - start_time)
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name=self.name, duration=time.time() - start_time)
