"""
tools.web - 网页工具集
Inspired by claw-code's web tools
需要: pip install aiohttp
"""
from __future__ import annotations
import re
import time
from .base import Tool, ToolResult, ToolCategory


class WebSearchTool(Tool):
    """网页搜索 (DuckDuckGo)"""
    name = "web_search"
    description = "Search the web for information."
    category = ToolCategory.WEB
    
    parameters = [
        {"name": "query", "description": "The search query", "type": "string", "required": True},
        {"Name": "max_results", "description": "Maximum number of results", "type": "integer", "required": False},
    ]
    
    async def execute(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
        import aiohttp
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_redirect": 1},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        return ToolResult(success=False, error=f"Search failed: HTTP {resp.status}", tool_name=self.name, duration=time.time() - start_time)
                    
                    data = await resp.json()
                    results = []
                    for topic in data.get("RelatedTopics", [])[:max_results]:
                        if topic.get("Text"):
                            results.append(f"- {topic['Text'][:100]}\n  {topic.get('FirstURL', '')}")
                    
                    return ToolResult(
                        success=True,
                        output="\n\n".join(results) if results else "No results found",
                        tool_name=self.name,
                        duration=time.time() - start_time,
                        metadata={"query": query, "results": len(results)}
                    )
        except Exception as e:
            return ToolResult(success=False, error=f"Network error: {e}", tool_name=self.name, duration=time.time() - start_time)


class WebFetchTool(Tool):
    """网页内容抓取"""
    name = "web_fetch"
    description = "Fetch and extract content from a URL."
    category = ToolCategory.WEB
    
    parameters = [
        {"name": "url", "description": "URL to fetch", "type": "string", "required": True},
        {"name": "max_length", "description": "Maximum content length", "type": "integer", "required": False},
    ]
    
    async def execute(self, url: str, max_length: int = 10000, **kwargs) -> ToolResult:
        import aiohttp
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return ToolResult(success=False, error=f"Fetch failed: HTTP {resp.status}", tool_name=self.name, duration=time.time() - start_time)
                    
                    content_type = resp.headers.get("Content-Type", "")
                    if "text/html" not in content_type and "text/plain" not in content_type:
                        return ToolResult(success=False, error=f"Unsupported content type: {content_type}", tool_name=self.name, duration=time.time() - start_time)
                    
                    text = await resp.text()
                    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
                    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                    text = re.sub(r'<[^>]+>', ' ', text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    if len(text) > max_length:
                        text = text[:max_length] + f"\n... [truncated, {len(text)} total chars]"
                    
                    return ToolResult(success=True, output=text, tool_name=self.name, duration=time.time() - start_time, metadata={"url": url})
        except Exception as e:
            return ToolResult(success=False, error=f"Network error: {e}", tool_name=self.name, duration=time.time() - start_time)
