# config.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ModelConfig:
    """大模型配置"""
    name: str
    api_base: str
    api_key_env: str
    model_name: str
    support_multimodal: bool = False

# 支持的大模型列表
SUPPORTED_MODELS: List[ModelConfig] = [
    ModelConfig(
        name="DeepSeek-V3",
        api_base="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-chat",
        support_multimodal=False
    ),
    ModelConfig(
        name="DeepSeek-R1",
        api_base="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-reasoner",
        support_multimodal=False
    ),
    ModelConfig(
        name="Qwen-Max",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        model_name="qwen-max",
        support_multimodal=True
    ),
    ModelConfig(
        name="Ollama-Local",
        api_base="http://localhost:11434/v1",
        api_key_env="",
        model_name="llama3",
        support_multimodal=False
    ),
    ModelConfig(
        name="GPT-4V",
        api_base="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        model_name="gpt-4-vision-preview",
        support_multimodal=True
    ),
]

# 用例字段定义
CASE_FIELDS = [
    "序号", "编号", "用例名称", "模块", "类型",
    "前置条件", "步骤", "测试数据", "预期结果", "优先级"
]

# 导出格式
EXPORT_FORMATS = ["markdown", "excel", "word"]