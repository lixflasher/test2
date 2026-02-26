import json
import asyncio
from openai import AsyncOpenAI
from utils.logger import logger
from utils.config import CONF

class LLMJudge:
    def __init__(self):
        llm_conf = CONF.llm
        self.client = AsyncOpenAI(
            base_url=llm_conf.get('api_base'),
            api_key=llm_conf.get('api_key')
        )
        self.model = llm_conf.get('model')
        self.temperature = llm_conf.get('temperature', 0.3)
        self.max_tokens = llm_conf.get('max_tokens', 500)

    async def judge(self, book_data, search_results=""):
        prompt = self._build_prompt(book_data, search_results)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"} # Force JSON if supported
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"LLM Judge error for {book_data.get('title')}: {e}")
            return None

    def _build_prompt(self, book, search_results):
        return f"""
你是一个网文分析专家。根据以下信息判断这本小说是否为"多女主文"。
多女主文的定义：主角有多个女性伴侣/恋人/红颜知己，且这些女性角色在剧情中有重要戏份。

书名：{book.get('title')}
作者：{book.get('author')}
标签：{', '.join(book.get('tags', []) + book.get('all_tags', []))}
简介：{book.get('full_synopsis') or book.get('rank_intro')}
免费章节内容摘要：{book.get('free_chapters_summary', '')[:1000]}
网络评价：{search_results}

请回答：
1. 是否为多女主文？(是/否/不确定)
2. 置信度 (0-100)
3. 判断理由（一句话）

严格按JSON格式输出：
{{"is_multi_heroine": true/false/null, "confidence": 0-100, "reason": "..."}}
"""

    def _parse_response(self, content):
        try:
            # Clean markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from LLM response: {content}")
            return None
