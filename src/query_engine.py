#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Engine - 查询引擎

意图理解和路由分发
灵感来源: claw-code/src/query_engine.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import logging


class QueryType(Enum):
    """查询类型"""
    CODE_GENERATION = "code_generation"
    CODE_UNDERSTANDING = "code_understanding"
    CODE_SEARCH = "code_search"
    CODE_MODIFICATION = "code_modification"
    PROJECT_QUERY = "project_query"
    SYSTEM_QUERY = "system_query"
    UNKNOWN = "unknown"


class Complexity(Enum):
    """任务复杂度"""
    TRIVIAL = "trivial"       # 简单操作
    SIMPLE = "simple"         # 简单任务
    MODERATE = "moderate"     # 中等任务
    COMPLEX = "complex"       # 复杂任务
    CRITICAL = "critical"    # 关键任务


@dataclass
class QueryContext:
    """查询上下文"""
    query: str
    query_type: QueryType = QueryType.UNKNOWN
    complexity: Complexity = Complexity.MODERATE
    requires_llm: bool = False
    tools_needed: list[str] = field(default_factory=list)
    estimated_steps: int = 1
    metadata: dict = field(default_factory=dict)


@dataclass  
class QueryResult:
    """查询结果"""
    success: bool
    query_type: QueryType
    complexity: Complexity
    routing_path: str
    confidence: float
    execution_plan: Optional[list[str]] = None
    warnings: list[str] = field(default_factory=list)


class QueryEngine:
    """
    查询引擎
    
    理解用户查询，决定执行路径
    """
    
    def __init__(self, llm_enabled: bool = False):
        self.llm_enabled = llm_enabled
        self.logger = logging.getLogger(__name__)
        
        # 查询模式注册表
        self.patterns: dict[QueryType, list[tuple[str, float]]] = {
            QueryType.CODE_GENERATION: [
                ("创建", 0.9),
                ("实现", 0.9),
                ("生成代码", 0.95),
                ("写一个", 0.8),
                ("create", 0.9),
                ("implement", 0.9),
                ("generate", 0.9),
            ],
            QueryType.CODE_MODIFICATION: [
                ("修改", 0.9),
                ("更新", 0.85),
                ("编辑", 0.8),
                ("modify", 0.9),
                ("update", 0.85),
            ],
            QueryType.CODE_UNDERSTANDING: [
                ("理解", 0.9),
                ("分析", 0.85),
                ("解释", 0.9),
                ("understand", 0.9),
                ("analyze", 0.85),
            ],
            QueryType.CODE_SEARCH: [
                ("搜索", 0.95),
                ("查找", 0.9),
                ("查找代码", 0.95),
                ("search", 0.95),
                ("find", 0.9),
            ],
            QueryType.PROJECT_QUERY: [
                ("项目", 0.8),
                ("结构", 0.75),
                ("project", 0.8),
                ("structure", 0.75),
            ],
            QueryType.SYSTEM_QUERY: [
                ("状态", 0.9),
                ("配置", 0.85),
                ("system", 0.9),
                ("config", 0.85),
            ]
        }
        
        # 复杂度关键词
        self.complexity_keywords = {
            Complexity.TRIVIAL: [r"简单", r"只是", r"just"],
            Complexity.SIMPLE: [r"一个", r"单个", r"one"],
            Complexity.MODERATE: [r"一些", r"多个", r"several"],
            Complexity.COMPLEX: [r"复杂", r"多个", r"complex"],
            Complexity.CRITICAL: [r"关键", r"重要", r"critical"],
        }
    
    def analyze(self, query: str) -> QueryContext:
        """
        分析查询
        
        Args:
            query: 用户查询
            
        Returns:
            QueryContext: 查询上下文
        """
        self.logger.debug(f"Analyzing query: {query}")
        
        # 检测查询类型
        query_type = self._classify_query(query)
        
        # 评估复杂度
        complexity = self._assess_complexity(query)
        
        # 判断是否需要LLM
        requires_llm = self._needs_llm(query_type, complexity)
        
        # 估算执行步骤
        estimated_steps = self._estimate_steps(complexity)
        
        # 确定需要的工具
        tools_needed = self._determine_tools(query_type, query)
        
        return QueryContext(
            query=query,
            query_type=query_type,
            complexity=complexity,
            requires_llm=requires_llm,
            tools_needed=tools_needed,
            estimated_steps=estimated_steps
        )
    
    def _classify_query(self, query: str) -> QueryType:
        """分类查询"""
        query_lower = query.lower()
        best_match = QueryType.UNKNOWN
        best_score = 0.0
        
        for qtype, patterns in self.patterns.items():
            score = 0.0
            for pattern, weight in patterns:
                if pattern.lower() in query_lower:
                    score += weight
            
            if score > best_score:
                best_score = score
                best_match = qtype
        
        return best_match
    
    def _assess_complexity(self, query: str) -> Complexity:
        """评估复杂度"""
        for complexity, keywords in self.complexity_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return complexity
        return Complexity.MODERATE
    
    def _needs_llm(self, query_type: QueryType, complexity: Complexity) -> bool:
        """判断是否需要LLM"""
        if not self.llm_enabled:
            return False
        
        # 代码生成通常需要LLM
        if query_type in [QueryType.CODE_GENERATION, QueryType.CODE_UNDERSTANDING]:
            return True
        
        # 复杂任务需要LLM
        if complexity in [Complexity.COMPLEX, Complexity.CRITICAL]:
            return True
        
        return False
    
    def _estimate_steps(self, complexity: Complexity) -> int:
        """估算执行步骤"""
        steps_map = {
            Complexity.TRIVIAL: 1,
            Complexity.SIMPLE: 2,
            Complexity.MODERATE: 3,
            Complexity.COMPLEX: 5,
            Complexity.CRITICAL: 8,
        }
        return steps_map.get(complexity, 3)
    
    def _determine_tools(self, query_type: QueryType, query: str) -> list[str]:
        """确定需要的工具"""
        tool_map = {
            QueryType.CODE_GENERATION: ["editor", "linter"],
            QueryType.CODE_MODIFICATION: ["editor", "linter", "tester"],
            QueryType.CODE_UNDERSTANDING: ["reader", "analyzer"],
            QueryType.CODE_SEARCH: ["searcher", "reader"],
            QueryType.PROJECT_QUERY: ["explorer", "reader"],
            QueryType.SYSTEM_QUERY: ["system_info"],
        }
        
        base_tools = tool_map.get(query_type, ["generic"])
        
        # 根据关键词添加额外工具
        if any(kw in query for kw in ["测试", "test"]):
            base_tools.append("tester")
        if any(kw in query for kw in ["部署", "deploy"]):
            base_tools.append("deployer")
        
        return base_tools
    
    def route(self, context: QueryContext) -> QueryResult:
        """
        路由决策
        
        Args:
            context: 查询上下文
            
        Returns:
            QueryResult: 路由结果
        """
        # 生成路由路径
        routing_path = self._generate_routing_path(context)
        
        # 生成执行计划
        execution_plan = self._generate_plan(context)
        
        return QueryResult(
            success=True,
            query_type=context.query_type,
            complexity=context.complexity,
            routing_path=routing_path,
            confidence=0.85,
            execution_plan=execution_plan
        )
    
    def _generate_routing_path(self, context: QueryContext) -> str:
        """生成路由路径"""
        return f"engine.{context.query_type.value}.{context.complexity.value}"
    
    def _generate_plan(self, context: QueryContext) -> list[str]:
        """生成执行计划"""
        plan = []
        
        # 1. 准备阶段
        if context.tools_needed:
            plan.append(f"load_tools({','.join(context.tools_needed)})")
        
        # 2. 执行阶段
        if context.requires_llm:
            plan.append("invoke_llm()")
        
        plan.append(f"execute_{context.query_type.value}()")
        
        # 3. 验证阶段
        plan.append("validate_result()")
        
        return plan


class SmartQueryEngine(QueryEngine):
    """
    智能查询引擎 - 支持LLM增强
    
    在基础QueryEngine上添加LLM理解能力
    """
    
    def __init__(self, llm_client=None):
        super().__init__(llm_enabled=llm_client is not None)
        self.llm_client = llm_client
    
    async def analyze_with_llm(self, query: str) -> QueryContext:
        """使用LLM增强分析"""
        if not self.llm_client:
            return self.analyze(query)
        
        # LLM增强的意图理解
        prompt = f"""
分析以下开发任务，返回JSON格式的意图分析：

任务: {query}

请返回：
- intent_type: 代码生成/代码理解/代码修改/代码搜索/项目查询/系统查询
- complexity: 简单/中等/复杂/关键
- required_tools: 需要的工具列表
- suggested_steps: 建议的执行步骤
"""
        
        # 调用LLM
        response = await self.llm_client.complete(prompt)
        
        # 解析LLM响应
        # ... 解析逻辑
        
        return self.analyze(query)
