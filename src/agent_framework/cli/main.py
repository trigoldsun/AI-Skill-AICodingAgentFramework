"""
CLI 主入口
Inspired by claw-code's CLI
"""
from __future__ import annotations
import asyncio
import sys


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI Coding Agent Framework")
    parser.add_argument("command", nargs="?", help="doctor, prompt, test")
    parser.add_argument("query", nargs="*", help="Query text")
    parser.add_argument("--model", "-m", default="sonnet", help="Model to use")
    args = parser.parse_args()
    
    query = " ".join(args.query)
    
    if args.command == "doctor":
        from .doctor import run_doctor, format_doctor_report
        checks = await run_doctor()
        print(format_doctor_report(checks))
        return 0
    
    elif args.command == "test":
        from ..mocks import run_parity_harness
        return await run_parity_harness()
    
    elif args.command == "prompt" and query:
        print(f"Prompt: {query}")
        print("(Requires API key: export ANTHROPIC_API_KEY=...)")
        return 0
    
    else:
        print("""
🦞 AI Coding Agent Framework v1.1.0

Usage:
  python -m agent_framework doctor           # Health check
  python -m agent_framework test             # Run parity harness
  python -m agent_framework prompt "..."     # One-shot prompt
  python -m agent_framework                  # REPL mode

Install:
  pip install -e .
  pip install aiohttp
  
Set API Key:
  export ANTHROPIC_API_KEY="sk-ant-..."
""")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
