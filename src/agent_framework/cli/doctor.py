"""
cli.doctor - /doctor 健康检查
Inspired by claw-code's /doctor command
"""
from __future__ import annotations
import os
import sys
import importlib
from pathlib import Path
from dataclasses import dataclass


@dataclass
class DoctorCheck:
    name: str
    status: str
    message: str
    details: str = ""


async def run_doctor() -> list:
    checks = []
    
    # Python 版本
    checks.append(DoctorCheck(
        name="Python 版本",
        status="✅" if sys.version_info >= (3, 10) else "❌",
        message=f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    ))
    
    # aiohttp
    try:
        mod = importlib.import_module("aiohttp")
        checks.append(DoctorCheck(name="aiohttp", status="✅", message=f"Installed: {mod.__version__}"))
    except ImportError:
        checks.append(DoctorCheck(name="aiohttp", status="⚠️", message="Not installed", details="pip install aiohttp"))
    
    # Anthropic API Key
    if os.environ.get("ANTHROPIC_API_KEY"):
        key = os.environ["ANTHROPIC_API_KEY"]
        checks.append(DoctorCheck(name="Anthropic API Key", status="✅", message=f"Present (sk-ant-...{key[-4:]})"))
    elif os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        checks.append(DoctorCheck(name="Anthropic Auth Token", status="✅", message="Present (OAuth/Bearer)"))
    else:
        checks.append(DoctorCheck(name="Anthropic API Key", status="⚠️", message="Not configured", details="Set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN"))
    
    # OpenAI API Key
    if os.environ.get("OPENAI_API_KEY"):
        checks.append(DoctorCheck(name="OpenAI API Key", status="✅", message="Present"))
    else:
        checks.append(DoctorCheck(name="OpenAI API Key", status="⚠️", message="Not configured (optional)"))
    
    # Working Directory
    cwd = Path.cwd()
    checks.append(DoctorCheck(name="Working Directory", status="✅", message=str(cwd)))
    
    # CLAUDE.md
    claude_md = cwd / "CLAUDE.md"
    if claude_md.exists():
        checks.append(DoctorCheck(name="CLAUDE.md", status="✅", message="Found"))
    else:
        checks.append(DoctorCheck(name="CLAUDE.md", status="⚠️", message="Not found", details="Optional: Create CLAUDE.md for project context"))
    
    # Tools
    try:
        from ..tools import create_default_pool
        pool = create_default_pool()
        tools = pool.list_all()
        checks.append(DoctorCheck(name="Built-in Tools", status="✅", message=f"{len(tools)} tools: {', '.join(tools)}"))
    except ImportError as e:
        checks.append(DoctorCheck(name="Built-in Tools", status="❌", message="Failed to load", details=str(e)))
    
    # Providers
    try:
        from ..providers import get_available_providers, MODEL_ALIASES
        providers = get_available_providers()
        if providers:
            checks.append(DoctorCheck(name="LLM Providers", status="✅", message=f"Available: {', '.join(providers)}"))
        else:
            checks.append(DoctorCheck(name="LLM Providers", status="❌", message="No providers configured", details="Set at least one API key"))
        
        checks.append(DoctorCheck(name="Model Aliases", status="✅", message=f"opus, sonnet, haiku, grok, grok-mini"))
    except ImportError as e:
        checks.append(DoctorCheck(name="LLM Providers", status="❌", message="Failed to load", details=str(e)))
    
    return checks


def format_doctor_report(checks: list) -> str:
    lines = ["=" * 50, "🦞 AI Coding Agent Framework - Health Check", "=" * 50, ""]
    
    for check in checks:
        lines.append(f"{check.status} {check.name}")
        lines.append(f"   {check.message}")
        if check.details:
            lines.append(f"   → {check.details}")
        lines.append("")
    
    passed = sum(1 for c in checks if c.status == "✅")
    warnings = sum(1 for c in checks if c.status == "⚠️")
    failed = sum(1 for c in checks if c.status == "❌")
    
    lines.append("-" * 50)
    lines.append(f"Summary: {passed} passed, {warnings} warnings, {failed} failed")
    lines.append("=" * 50)
    
    return "\n".join(lines)
