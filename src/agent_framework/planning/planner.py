"""
planning.planner - LLM 驱动的任务规划器
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..providers.base import BaseLLMProvider, Message


AVAILABLE_STEPS = [
    "read_files", "analyze_requirements", "search_code",
    "generate_code", "write_file", "edit_file", "bash",
    "run_tests", "validate", "report",
]


PLANNING_PROMPT = """你是一个任务规划专家。用户请求：「{query}」

请将任务分解为具体的执行步骤。返回 JSON 格式：
{{
  "summary": "任务总结",
  "steps": [
    {{
      "name": "step_name",
      "description": "步骤描述",
      "tool": "使用的工具（可选）",
      "args": {{"参数": "值"}},
      "depends_on": ["前置步骤名"]
    }}
  ]
}}

可用步骤类型：
{available_steps}

要求：
1. 步骤要具体、可执行
2. 考虑依赖关系（depends_on）
3. 先了解现状再行动（先 read_files）
4. 最后验证结果（validate/report）
5. JSON 必须合法
"""


@dataclass
class PlanStep:
    name: str
    description: str
    tool: Optional[str] = None
    args: dict = field(default_factory=dict)
    depends_on: list = field(default_factory=list)


@dataclass
class ExecutionPlan:
    steps: list
    summary: str = ""


class Planner:
    """LLM 驱动的任务规划器"""
    
    def __init__(self, llm_provider: "BaseLLMProvider"):
        self.llm = llm_provider
    
    async def plan(self, query: str, context: dict = None) -> ExecutionPlan:
        """根据查询生成执行计划"""
        context_str = ""
        if context:
            context_str = "\n\n上下文信息：\n" + "\n".join(f"- {k}: {v}" for k, v in context.items())
        
        prompt = PLANNING_PROMPT.format(
            query=query + context_str,
            available_steps="\n".join(f"- {s}" for s in AVAILABLE_STEPS)
        )
        
        try:
            from ..providers.base import Message
            messages = [Message(role="user", content=prompt)]
            response = await self.llm.chat(messages, max_tokens=2048)
            
            plan_text = response.content.strip()
            if "```json" in plan_text:
                start = plan_text.find("```json") + 7
                end = plan_text.find("```", start)
                plan_text = plan_text[start:end]
            elif "```" in plan_text:
                start = plan_text.find("```") + 3
                end = plan_text.find("```", start)
                plan_text = plan_text[start:end]
            
            plan_data = json.loads(plan_text.strip())
            
            steps = []
            for step_data in plan_data.get("steps", []):
                steps.append(PlanStep(
                    name=step_data["name"],
                    description=step_data.get("description", ""),
                    tool=step_data.get("tool"),
                    args=step_data.get("args", {}),
                    depends_on=step_data.get("depends_on", []),
                ))
            
            return ExecutionPlan(steps=steps, summary=plan_data.get("summary", ""))
            
        except json.JSONDecodeError:
            return ExecutionPlan(
                steps=[
                    PlanStep(name="analyze_requirements", description=f"分析需求：{query}"),
                    PlanStep(name="report", description="汇报结果"),
                ],
                summary=f"分析并处理请求：{query}",
            )
        except Exception as e:
            raise RuntimeError(f"Planning failed: {e}")
