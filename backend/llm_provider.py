import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional

def load_dotenv():
    """Lightweight built-in .env / env file parser."""
    root_dir = Path(__file__).resolve().parent.parent
    for env_name in [".env", "env"]:
        env_file = root_dir / env_name
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")

load_dotenv()

class LLMProvider:
    """
    Multi-provider LLM Client supporting Groq (openai/gpt-oss-120b, openai/gpt-oss-20b, llama-3.3-70b-versatile),
    OpenAI (gpt-4o-mini), and Gemini.
    """
    def __init__(self):
        load_dotenv()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

    def is_available(self) -> bool:
        load_dotenv()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        return bool(self.groq_api_key or self.openai_api_key or self.gemini_api_key)

    def generate_grounded_answer(
        self,
        query: str,
        evidence_chunks: List[Dict[str, Any]],
        language: str = "en",
        city_name: str = "Hampi"
    ) -> Optional[str]:
        load_dotenv()
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        if not evidence_chunks or not self.is_available():
            return None

        evidence_text = "\n\n".join([
            f"--- SOURCE: {c.get('source', 'Official Registry')} ---\nTITLE: {c.get('title')}\nCONTENT: {c.get('content')}"
            for c in evidence_chunks
        ])

        lang_instruction = "Respond in English."
        if language == "kn":
            lang_instruction = "Respond in natural, fluent Kannada (ಕನ್ನಡ) keeping proper nouns (e.g. Vittala Temple, Virupaksha Temple) intact."
        elif language == "hi":
            lang_instruction = "Respond in natural, fluent Hindi (हिन्दी) keeping proper nouns intact."

        system_prompt = f"""You are GeoGuide, a verified, location-aware travel AI companion for {city_name}.
STRICT GROUNDING RULES:
1. Answer the user's question using ONLY the facts and schedules present in the retrieved verified evidence below.
2. If the user asks whether a place is open, closed, or operating right now or today, always state its official operating hours/timings and any relevant advisories or status details present in the evidence.
3. For ticketing, fee, or pricing inquiries, always include the specific entry fee amounts (e.g. ₹ amounts) and covered monuments mentioned in the evidence.
4. If no relevant information about the place or topic exists in the evidence, state: "GeoGuide couldn't verify that from its available sources."
5. Never invent prices, dates, rules, or historical details.
6. Keep the answer concise, friendly, and structured.
7. {lang_instruction}"""

        user_content = f"""RETRIEVED EVIDENCE:
{evidence_text}

USER QUESTION:
{query}"""

        # 1. Try Groq (Supported models in priority order)
        if self.groq_api_key:
            groq_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
            for model_name in groq_models:
                try:
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.groq_api_key.strip()}",
                        "Content-Type": "application/json",
                        "User-Agent": "curl/7.68.0"
                    }
                    payload = {
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 500
                    }
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
                    with urllib.request.urlopen(req, timeout=8) as response:
                        res_data = json.loads(response.read().decode('utf-8'))
                        ans = res_data["choices"][0]["message"]["content"].strip()
                        if ans:
                            return ans
                except urllib.error.HTTPError as e:
                    continue
                except Exception as e:
                    print(f"[GeoGuide LLMProvider] Groq call exception with {model_name}: {e}")
                    continue

        # 2. Try OpenAI (GPT-4o-mini)
        if self.openai_api_key:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key.strip()}",
                    "Content-Type": "application/json",
                    "User-Agent": "GeoGuide/2.0"
                }
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
                with urllib.request.urlopen(req, timeout=6) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    return res_data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"[GeoGuide LLMProvider] OpenAI call error: {e}")

        return None
