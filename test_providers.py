#!/usr/bin/env python3
"""
Debug script to test AI provider configuration
Run this to diagnose issues with your setup
"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("AI PROVIDER DIAGNOSTIC SCRIPT")
print("=" * 60)

# 1. Check if .env file exists
env_file = Path(".env")
print(f"1. .env file exists: {env_file.exists()}")
if env_file.exists():
    print(f"   .env file path: {env_file.absolute()}")
    print(f"   .env file size: {env_file.stat().st_size} bytes")
else:
    print("   ❌ .env file not found!")

print()

# 2. Try to load dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("2. ✅ python-dotenv loaded successfully")
except ImportError:
    print("2. ❌ python-dotenv not installed! Run: pip install python-dotenv")
    sys.exit(1)

print()

# 3. Check environment variables
print("3. Environment Variables:")
github_token = os.getenv("GITHUB_TOKEN")
gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

print(f"   GITHUB_TOKEN: {'✅ Set' if github_token else '❌ Not set'}")
if github_token:
    print(f"   GITHUB_TOKEN length: {len(github_token)} chars")
    print(f"   GITHUB_TOKEN starts with: {github_token[:10]}...")

print(f"   GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Not set'}")
if gemini_key:
    print(f"   GEMINI_API_KEY length: {len(gemini_key)} chars")

print(f"   OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")

print()

# 4. Test package imports
print("4. Package Availability:")
try:
    import google.generativeai as genai
    print("   ✅ google-generativeai available")
    GEMINI_AVAILABLE = True
except ImportError:
    print("   ❌ google-generativeai not available")
    GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    print("   ✅ openai package available")
    OPENAI_AVAILABLE = True
except ImportError:
    print("   ❌ openai package not available")
    OPENAI_AVAILABLE = False

print()

# 5. Test connections
print("5. Connection Tests:")

# Test GitHub Models
if github_token and OPENAI_AVAILABLE:
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=github_token,
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print("   ✅ GitHub Models: Connection successful!")
        print(f"   Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"   ❌ GitHub Models: Failed - {e}")
        # Check specific error types
        if "401" in str(e) or "unauthorized" in str(e).lower():
            print("      → This looks like an authentication error. Check your GitHub token.")
        elif "403" in str(e) or "forbidden" in str(e).lower():
            print("      → This might be a permissions issue. Ensure your token has 'repo' scope.")
elif not github_token:
    print("   ⚠️  GitHub Models: Skipped (no GITHUB_TOKEN)")
elif not OPENAI_AVAILABLE:
    print("   ⚠️  GitHub Models: Skipped (openai package not installed)")

# Test Gemini
if gemini_key and GEMINI_AVAILABLE:
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hi")
        print("   ✅ Gemini: Connection successful!")
        print(f"   Response: {response.text[:50]}...")
    except Exception as e:
        print(f"   ❌ Gemini: Failed - {e}")
elif not gemini_key:
    print("   ⚠️  Gemini: Skipped (no GEMINI_API_KEY)")
elif not GEMINI_AVAILABLE:
    print("   ⚠️  Gemini: Skipped (google-generativeai not installed)")

print()

# 6. Recommendations
print("6. Recommendations:")
if not github_token and not gemini_key:
    print("   ❌ No API keys configured!")
    print("   → Set up GitHub Models (recommended):")
    print("     1. Go to https://github.com/settings/tokens")
    print("     2. Create new token with 'repo' scope")
    print("     3. Add to .env: GITHUB_TOKEN=your_token_here")
elif github_token and not OPENAI_AVAILABLE:
    print("   → Install OpenAI package: pip install openai")
elif gemini_key and not GEMINI_AVAILABLE:
    print("   → Install Gemini package: pip install google-generativeai")

print("\n" + "=" * 60)
print("Debug complete! Check the results above.")
print("=" * 60)