import os
import httpx

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = os.getenv('GEMINI_API_URL', 'AIzaSyBsN9IJpwB-oFsM4oX84PNVxd7X4ekHghM')  # placeholder URL, replace with actual endpoint

def generate_narrative(prompt: str) -> str:
    """Call Gemini API to enhance narrative. If API key missing, return prompt as-is."""
    if not prompt:
        return ''
    if not GEMINI_API_KEY:
        return prompt

    headers = {'Authorization': f'Bearer {GEMINI_API_KEY}', 'Content-Type': 'application/json'}
    payload = {'prompt': prompt, 'max_tokens': 256}
    try:
        r = httpx.post(GEMINI_API_URL, json=payload, headers=headers, timeout=30.0)
        r.raise_for_status()
        data = r.json()
        return data.get('text') or prompt
    except Exception:
        return prompt
