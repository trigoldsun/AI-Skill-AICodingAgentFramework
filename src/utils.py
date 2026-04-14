#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils - 工具函数
"""

import os
import json
import logging
from pathlib import Path
from typing import Any


def setup_logging(level: str = "INFO", log_file: str = None):
    """
    设置日志
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def load_config(config_path: str = None) -> dict:
    """
    加载配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        dict: 配置字典
    """
    if not config_path:
        config_path = os.environ.get("AGENT_CONFIG", "config.json")
    
    path = Path(config_path)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    
    return {}


def ensure_dir(path: str):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)


def read_file(path: str) -> str:
    """读取文件"""
    with open(path, encoding='utf-8') as f:
        return f.read()


def write_file(path: str, content: str):
    """写入文件"""
    ensure_dir(str(Path(path).parent))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
