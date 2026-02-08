import os
import httpx

# Get API key from environment. You can set GEMINI_API_KEY in .env or environment.
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

def generate_narrative(prompt: str) -> str:
    """Call Google Gemini API to generate an enhanced incident narrative.
    
    If API key is missing or call fails, returns the original prompt as a fallback.
    """
    if not prompt:
        return ''
    if not GEMINI_API_KEY:
        # Return a basic formatted narrative when no API key is available
        return _fallback_narrative(prompt)

    # Google Generative AI REST API endpoint
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}'
    
    system_prompt = """You are a cybersecurity incident response analyst. 
Based on the following security log findings, generate a clear, concise narrative 
that explains what happened, identifies potential threats, and summarizes the security incident. 
Write in a professional but easy-to-understand style. Keep the narrative to 2-3 paragraphs."""

    payload = {
        'contents': [{
            'parts': [{
                'text': f"{system_prompt}\n\nFindings:\n{prompt}"
            }]
        }],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 500,
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        r = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        r.raise_for_status()
        data = r.json()
        # Extract text from Gemini response
        candidates = data.get('candidates', [])
        if candidates and 'content' in candidates[0]:
            parts = candidates[0]['content'].get('parts', [])
            if parts:
                return parts[0].get('text', prompt)
        return _fallback_narrative(prompt)
    except Exception as e:
        print(f"Gemini API error: {e}")
        return _fallback_narrative(prompt)


def _fallback_narrative(findings_text: str) -> str:
    """Generate a basic narrative when Gemini API is unavailable."""
    if not findings_text.strip():
        return "No significant security events were detected in the analyzed log file."
    
    return f"""**Security Incident Analysis**

The security log analysis has identified the following notable events:

{findings_text}

Review these findings carefully and take appropriate action based on your organization's incident response procedures."""
