# 从 config.py 导出，方便直接 from config import KEY, BASE_URL
from .config import KEY as ANTHROPIC_KEY, BASE_URL as ANTHROPIC_BASE_URL, MODEL as ANTHROPIC_MODEL
from .config_openai import KEY as OPENAI_KEY, BASE_URL as OPENAI_BASE_URL, MODEL as OPENAI_MODEL


def create_anthropic_client():
    """返回配置好 key 和 url 的 Anthropic 客户端"""
    from anthropic import Anthropic
    return Anthropic(api_key=ANTHROPIC_KEY, base_url=ANTHROPIC_BASE_URL)


def create_openai_client():
    """返回配置好 key 和 url 的 OpenAI 客户端"""
    from openai import OpenAI
    return OpenAI(api_key=OPENAI_KEY, base_url=OPENAI_BASE_URL)
