import json
import base64
import httpx


VISION_PROMPT = """Analyze this handwritten document image and extract ALL content into structured JSON.

Return ONLY valid JSON with this exact structure:
{
    "headings": ["list of headings/titles found"],
    "paragraphs": ["list of paragraph text blocks"],
    "questions": [
        {
            "question": "the question text",
            "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
            "answer": "the correct answer letter or text",
            "explanation": "explanation if present"
        }
    ],
    "formulas": ["list of math formulas in LaTeX notation"]
}

Instructions:
- Convert ALL handwritten text to typed text accurately
- Detect and preserve document structure (headings, paragraphs)
- Convert math expressions to LaTeX notation
- Extract questions with their options, answers, and explanations
- If no questions are found, return an empty questions array
- If no formulas found, return an empty formulas array
- Return ONLY the JSON, no other text"""


class HandwritingEngine:
    """Model-agnostic handwriting transcription using vision APIs."""

    def __init__(self, provider: str, api_key: str):
        self.provider = provider.lower()
        self.api_key = api_key

    def transcribe(self, image_bytes: bytes) -> dict:
        """Transcribe a handwritten page image to structured content."""
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        if self.provider == "gemini":
            return self._call_gemini(b64_image)
        elif self.provider == "openai":
            return self._call_openai(b64_image)
        elif self.provider == "anthropic":
            return self._call_anthropic(b64_image)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _parse_response(self, text: str) -> dict:
        """Parse JSON from model response, handling markdown code blocks."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (code fence markers)
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "headings": [],
                "paragraphs": [text],
                "questions": [],
                "formulas": [],
            }

    def _call_gemini(self, b64_image: str) -> dict:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": VISION_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": b64_image,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192},
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                url, json=payload, params={"key": self.api_key}
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_response(text)

    def _call_openai(self, b64_image: str) -> dict:
        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}"
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 8192,
            "temperature": 0.1,
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return self._parse_response(text)

    def _call_anthropic(self, b64_image: str) -> dict:
        url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 8192,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": b64_image,
                            },
                        },
                        {"type": "text", "text": VISION_PROMPT},
                    ],
                }
            ],
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                url,
                json=payload,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["content"][0]["text"]
            return self._parse_response(text)
