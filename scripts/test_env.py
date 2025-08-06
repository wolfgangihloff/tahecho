#!/usr/bin/env python3
"""Test script to verify environment variables are loaded correctly."""

import os

from dotenv import load_dotenv


def test_environment_variables():
    """Test if environment variables are loaded correctly."""
    print("🔍 Testing Environment Variables")
    print("=" * 40)

    # Load environment variables from .env file
    load_dotenv()

    # Check required variables for sitemap functionality
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API Key",
        "SUPABASE_URL": "Supabase URL",
        "SUPABASE_ANON_KEY": "Supabase Anonymous Key",
        "SUPABASE_SERVICE_ROLE_KEY": "Supabase Service Role Key (optional)",
    }

    print("Checking required environment variables:")
    print("-" * 40)

    all_present = True
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Mask the value for security
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var_name}: {masked_value}")
        else:
            print(f"❌ {var_name}: NOT SET")
            if var_name != "SUPABASE_SERVICE_ROLE_KEY":  # This one is optional
                all_present = False

    print("\n" + "=" * 40)

    if all_present:
        print("🎉 All required environment variables are set!")
        print("You can now run the sitemap functionality.")
    else:
        print("⚠️  Some required environment variables are missing.")
        print("Please add them to your .env file:")
        print()
        for var_name, description in required_vars.items():
            if not os.getenv(var_name) and var_name != "SUPABASE_SERVICE_ROLE_KEY":
                print(f"   {var_name}=your_value_here")

    # Check optional sitemap variables
    print("\nOptional sitemap variables:")
    print("-" * 40)
    optional_vars = {
        "SITEMAP_AGENTS_ENABLED": "Enable sitemap agents",
        "SITEMAP_URLS": "Comma-separated sitemap URLs",
        "EMBEDDING_MODEL": "OpenAI embedding model",
        "EMBEDDING_DIMENSION": "Embedding dimension",
    }

    for var_name, description in optional_vars.items():
        value = os.getenv(var_name)
        if value:
            print(f"✅ {var_name}: {value}")
        else:
            print(f"⚪ {var_name}: Not set (will use defaults)")


if __name__ == "__main__":
    test_environment_variables()
