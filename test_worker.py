"""Quick test to verify Python syntax"""
import json
from urllib.parse import urlparse, parse_qs

# 模拟 request.url
test_url = "http://localhost:8787/health"
parsed = urlparse(test_url)
print(f"path: {parsed.path}")
print(f"query: {parsed.query}")
print(f"parse_qs: {parse_qs(parsed.query)}")
print("✓ Syntax check passed!")
