def normalize_content(content) -> str:
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        texts = [
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        ]
        joined = "\n".join(t for t in texts if t)
        if joined:
            return joined
        
        return "".join(b.get("text", "") for b in content if isinstance(b, dict))
    
    return str(content)

def extract_text(response) -> str:
    return normalize_content(getattr(response, "content", response)).strip()