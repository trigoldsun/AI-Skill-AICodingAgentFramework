"""
Parser - Natural language parsing

Parses user input into structured commands.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class IntentType(Enum):
    """Intent classification"""
    CODE_GENERATION = "code_generation"
    CODE_MODIFICATION = "code_modification"
    CODE_QUERY = "code_query"
    SYSTEM_COMMAND = "system_command"
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Parsed user intent"""
    type: IntentType
    confidence: float
    entities: Dict[str, Any]
    raw_query: str


class Parser:
    """
    Natural language parser.

    Parses user queries into structured intents.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Intent patterns
        self._patterns = {
            IntentType.CODE_GENERATION: [
                r"create", r"implement", r"generate", r"build.*new"
            ],
            IntentType.CODE_MODIFICATION: [
                r"modify", r"update", r"edit", r"change", r"fix"
            ],
            IntentType.CODE_QUERY: [
                r"find", r"search", r"explain", r"what.*is"
            ],
            IntentType.SYSTEM_COMMAND: [
                r"/\w+", r"run.*command", r"execute"
            ],
        }

    def parse(self, query: str) -> ParsedIntent:
        """
        Parse a query into intent.

        Args:
            query: User query string

        Returns:
            ParsedIntent with classified intent
        """
        query_lower = query.lower()

        # Match patterns
        best_type = IntentType.UNKNOWN
        best_score = 0.0

        for intent_type, patterns in self._patterns.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1.0

            if score > best_score:
                best_score = score
                best_type = intent_type

        confidence = min(best_score / 2.0, 1.0)

        return ParsedIntent(
            type=best_type,
            confidence=confidence,
            entities={},
            raw_query=query
        )
