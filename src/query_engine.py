"""
Query Engine - Intent understanding and routing

Inspired by claw-code's query processing:
- Pattern-based intent classification
- Complexity assessment
- Tool selection
- Execution planning

Query Lifecycle:
    parse -> classify -> assess -> plan -> route
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class QueryType(Enum):
    """Query/intent classification"""
    CODE_GENERATION = "code_generation"
    CODE_UNDERSTANDING = "code_understanding"
    CODE_SEARCH = "code_search"
    CODE_MODIFICATION = "code_modification"
    PROJECT_QUERY = "project_query"
    SYSTEM_QUERY = "system_query"
    TASK_QUERY = "task_query"
    UNKNOWN = "unknown"


class Complexity(Enum):
    """Task complexity levels"""
    TRIVIAL = "trivial"      # Simple operation
    SIMPLE = "simple"        # Single step
    MODERATE = "moderate"     # Few steps
    COMPLEX = "complex"      # Multiple steps
    CRITICAL = "critical"    # Major undertaking


@dataclass
class QueryContext:
    """
    Structured query context after analysis.

    Attributes:
        query: Original query string
        query_type: Classified intent
        complexity: Assessed complexity
        requires_llm: Whether LLM is needed
        tools_needed: Selected tools
        estimated_steps: Estimated execution steps
        metadata: Additional context
    """
    query: str
    query_type: QueryType = QueryType.UNKNOWN
    complexity: Complexity = Complexity.MODERATE
    requires_llm: bool = False
    tools_needed: List[str] = field(default_factory=list)
    estimated_steps: int = 1
    metadata: dict = field(default_factory=dict)


@dataclass
class QueryResult:
    """Result of query routing"""
    success: bool
    query_type: QueryType
    complexity: Complexity
    routing_path: str
    confidence: float
    execution_plan: Optional[List[str]] = None
    warnings: List[str] = field(default_factory=list)


class QueryEngine:
    """
    Query analysis and intent routing.

    Inspired by claw-code's query processing:
    - Pattern matching for intent classification
    - Complexity scoring
    - Tool selection based on intent
    - Execution plan generation

    The query engine is the "brain" that decides:
    1. What the user wants to do
    2. How complex it is
    3. Which tools are needed
    4. How to execute it
    """

    def __init__(self, llm_enabled: bool = False):
        self.llm_enabled = llm_enabled
        self.logger = logging.getLogger(__name__)

        # Intent patterns with weights
        self._patterns: Dict[QueryType, List[tuple]] = {
            QueryType.CODE_GENERATION: [
                (r"create|implement|generate|write.*code|build.*new", 0.9),
                (r"add.*feature|make.*function|develop", 0.85),
                (r" scaffold | boilerplate | template ", 0.8),
            ],
            QueryType.CODE_MODIFICATION: [
                (r"modify|update|edit|change|refactor", 0.9),
                (r"fix|repair|debug|patch", 0.85),
                (r"improve|optimize|enhance", 0.8),
                (r"rename|move|copy", 0.75),
            ],
            QueryType.CODE_UNDERSTANDING: [
                (r"explain|understand|analyze|describe", 0.9),
                (r"what.*does|how.*work|why.*is", 0.85),
                (r"document|comment", 0.7),
            ],
            QueryType.CODE_SEARCH: [
                (r"search|find|grep|locate|look.*up", 0.95),
                (r"where.*is|find.*file|search.*for", 0.9),
            ],
            QueryType.PROJECT_QUERY: [
                (r"project.*structure|architecture|overview", 0.9),
                (r"list.*file|tree.*view|show.*dir", 0.8),
            ],
            QueryType.SYSTEM_QUERY: [
                (r"status|health|diagnostic|check", 0.9),
                (r"config|setting|preference", 0.85),
                (r"version|info|about", 0.8),
            ],
            QueryType.TASK_QUERY: [
                (r"task|job|to.do|assignment", 0.9),
                (r"progress|status.*task", 0.85),
            ],
        }

        # Complexity keywords
        self._complexity_keywords = {
            Complexity.TRIVIAL: [r"just|simply|quick", r"one.*file", r"single"],
            Complexity.SIMPLE: [r"simple|easy|basic", r"one.*step", r"straightforward"],
            Complexity.MODERATE: [r"several|some|multiple", r"few.*file", r"moderate"],
            Complexity.COMPLEX: [r"complex|complicated|advanced", r"multiple.*component", r"several.*step"],
            Complexity.CRITICAL: [r"critical|important|major", r"entire.*system", r"full.*rewrite"],
        }

    def analyze(self, query: str) -> QueryContext:
        """
        Analyze a query and return structured context.

        Args:
            query: Natural language query

        Returns:
            QueryContext with classified intent
        """
        self.logger.debug(f"Analyzing query: {query}")

        # Classify intent
        query_type = self._classify(query)

        # Assess complexity
        complexity = self._assess_complexity(query)

        # Determine if LLM needed
        requires_llm = self._needs_llm(query_type, complexity)

        # Select tools
        tools = self._select_tools(query_type, query)

        # Estimate steps
        steps = self._estimate_steps(complexity)

        return QueryContext(
            query=query,
            query_type=query_type,
            complexity=complexity,
            requires_llm=requires_llm,
            tools_needed=tools,
            estimated_steps=steps
        )

    def _classify(self, query: str) -> QueryType:
        """Classify query intent using pattern matching"""
        query_lower = query.lower()
        best_match = QueryType.UNKNOWN
        best_score = 0.0

        for qtype, patterns in self._patterns.items():
            score = 0.0
            for pattern, weight in patterns:
                if re.search(pattern, query_lower):
                    score += weight

            if score > best_score:
                best_score = score
                best_match = qtype

        self.logger.debug(f"Classified as {best_match.value} (confidence: {best_score:.2f})")
        return best_match

    def _assess_complexity(self, query: str) -> Complexity:
        """Assess task complexity"""
        query_lower = query.lower()

        for complexity, keywords in self._complexity_keywords.items():
            for keyword in keywords:
                if re.search(keyword, query_lower):
                    return complexity

        return Complexity.MODERATE

    def _needs_llm(self, query_type: QueryType, complexity: Complexity) -> bool:
        """Determine if LLM is needed for this query"""
        if not self.llm_enabled:
            return False

        # Code generation always benefits from LLM
        if query_type == QueryType.CODE_GENERATION:
            return True

        # Complex tasks need LLM
        if complexity in (Complexity.COMPLEX, Complexity.CRITICAL):
            return True

        # Understanding tasks need LLM
        if query_type == QueryType.CODE_UNDERSTANDING:
            return complexity != Complexity.TRIVIAL

        return False

    def _select_tools(self, query_type: QueryType, query: str) -> List[str]:
        """Select appropriate tools for the query"""
        # Base tool selection by query type
        tool_map = {
            QueryType.CODE_GENERATION: ["editor", "linter"],
            QueryType.CODE_MODIFICATION: ["editor", "linter", "tester"],
            QueryType.CODE_UNDERSTANDING: ["reader", "analyzer"],
            QueryType.CODE_SEARCH: ["searcher", "reader"],
            QueryType.PROJECT_QUERY: ["explorer", "reader"],
            QueryType.SYSTEM_QUERY: ["system_info"],
            QueryType.TASK_QUERY: ["task_manager"],
        }

        tools = tool_map.get(query_type, ["generic"])

        # Add context-sensitive tools
        query_lower = query.lower()

        if any(kw in query_lower for kw in ["test", "spec"]):
            tools.append("tester")
        if any(kw in query_lower for kw in ["deploy", "release", "build"]):
            tools.append("builder")
        if any(kw in query_lower for kw in ["git", "commit", "branch"]):
            tools.append("git")
        if any(kw in query_lower for kw in ["docker", "container"]):
            tools.append("docker")
        if any(kw in query_lower for kw in ["debug", "trace"]):
            tools.append("debugger")

        return list(set(tools))  # Remove duplicates

    def _estimate_steps(self, complexity: Complexity) -> int:
        """Estimate number of execution steps"""
        steps_map = {
            Complexity.TRIVIAL: 1,
            Complexity.SIMPLE: 2,
            Complexity.MODERATE: 3,
            Complexity.COMPLEX: 5,
            Complexity.CRITICAL: 8,
        }
        return steps_map.get(complexity, 3)

    def route(self, context: QueryContext) -> QueryResult:
        """
        Generate routing decision and execution plan.

        Args:
            context: Analyzed query context

        Returns:
            QueryResult with routing path and plan
        """
        # Generate routing path
        routing_path = f"engine.{context.query_type.value}.{context.complexity.value}"

        # Generate execution plan
        plan = self._generate_plan(context)

        # Assess confidence
        confidence = self._calculate_confidence(context)

        # Generate warnings
        warnings = self._generate_warnings(context)

        return QueryResult(
            success=True,
            query_type=context.query_type,
            complexity=context.complexity,
            routing_path=routing_path,
            confidence=confidence,
            execution_plan=plan,
            warnings=warnings
        )

    def _generate_plan(self, context: QueryContext) -> List[str]:
        """Generate execution plan"""
        plan = []

        # Validation step
        plan.append("validate_request")

        # Preparation
        if context.tools_needed:
            plan.append(f"load_tools({','.join(context.tools_needed)})")

        # LLM step if needed
        if context.requires_llm:
            plan.append("invoke_llm()")

        # Query-type specific steps
        type_steps = {
            QueryType.CODE_GENERATION: [
                "analyze_requirements",
                "generate_code",
                "validate_syntax",
                "format_code"
            ],
            QueryType.CODE_MODIFICATION: [
                "read_current_code",
                "apply_modifications",
                "validate_changes",
                "format_code"
            ],
            QueryType.CODE_UNDERSTANDING: [
                "read_files",
                "analyze_structure",
                "generate_explanation"
            ],
            QueryType.CODE_SEARCH: [
                "execute_search",
                "filter_results",
                "present_findings"
            ],
            QueryType.PROJECT_QUERY: [
                "explore_structure",
                "analyze_architecture",
                "generate_overview"
            ],
            QueryType.SYSTEM_QUERY: [
                "gather_system_info",
                "format_response"
            ],
            QueryType.TASK_QUERY: [
                "query_task_registry",
                "format_task_status"
            ],
        }

        plan.extend(type_steps.get(context.query_type, ["execute_generic"]))

        # Final validation
        plan.append("validate_result")

        return plan

    def _calculate_confidence(self, context: QueryContext) -> float:
        """Calculate routing confidence"""
        confidence = 0.7  # Base confidence

        # Higher confidence for clear patterns
        if context.query_type != QueryType.UNKNOWN:
            confidence += 0.15

        # Higher confidence for clear complexity signals
        if context.complexity in (Complexity.TRIVIAL, Complexity.CRITICAL):
            confidence += 0.1

        # Lower confidence if LLM would help but not available
        if context.requires_llm and not self.llm_enabled:
            confidence -= 0.1

        return min(confidence, 0.99)

    def _generate_warnings(self, context: QueryContext) -> List[str]:
        """Generate warnings for the execution"""
        warnings = []

        if context.requires_llm and not self.llm_enabled:
            warnings.append("LLM recommended but not enabled - results may be limited")

        if context.complexity == Complexity.CRITICAL:
            warnings.append("This is a critical task - consider breaking it into smaller steps")

        if len(context.tools_needed) > 4:
            warnings.append("Many tools required - consider simplifying the request")

        return warnings


class SmartQueryEngine(QueryEngine):
    """
    LLM-enhanced query engine.

    When an LLM client is available, uses it to:
    - Improve intent classification
    - Better complexity assessment
    - More accurate tool selection
    """

    def __init__(self, llm_client=None):
        super().__init__(llm_enabled=llm_client is not None)
        self.llm_client = llm_client

    async def analyze_with_llm(self, query: str) -> QueryContext:
        """
        Analyze query using LLM for better understanding.

        Args:
            query: Natural language query

        Returns:
            Enhanced QueryContext
        """
        if not self.llm_client:
            return self.analyze(query)

        # Use LLM to analyze
        prompt = f"""Analyze this development task and return a JSON object:

Task: {query}

Return JSON with:
- query_type: one of [code_generation, code_understanding, code_search, code_modification, project_query, system_query]
- complexity: one of [trivial, simple, moderate, complex, critical]
- tools_needed: array of tool names
- suggested_steps: number of estimated steps
- rationale: brief explanation
"""

        try:
            response = await self.llm_client.complete(prompt)
            # Parse response and create enhanced context
            # For now, fall back to pattern matching
            return self.analyze(query)
        except Exception:
            return self.analyze(query)
