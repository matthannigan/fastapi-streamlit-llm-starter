#!/usr/bin/env python3
"""Generate secure API keys for the authentication system."""

import secrets
import string
import argparse
import sys

def generate_api_key(length: int = 32, prefix: str = "sk") -> str:
    """
    Generate a cryptographically secure API key.
    
    Args:
        length: Length of the random part (default: 32)
        prefix: Prefix for the key (default: "sk")
        
    Returns:
        Generated API key
    """
    # Generate random hex string
    random_part = secrets.token_hex(length)
    
    # Combine with prefix
    if prefix:
        return f"{prefix}-{random_part}"
    else:
        return random_part

def generate_multiple_keys(count: int, length: int = 32, prefix: str = "sk") -> list:
    """Generate multiple API keys."""
    return [generate_api_key(length, prefix) for _ in range(count)]

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate secure API keys for authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_api_key.py                    # Generate one key with default settings
  python generate_api_key.py -c 3               # Generate 3 keys
  python generate_api_key.py -l 16 -p "api"     # Generate key with length 16 and prefix "api"
  python generate_api_key.py -c 5 --no-prefix   # Generate 5 keys without prefix
        """
    )
    
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=1,
        help="Number of keys to generate (default: 1)"
    )
    
    parser.add_argument(
        "-l", "--length",
        type=int,
        default=32,
        help="Length of the random part in bytes (default: 32)"
    )
    
    parser.add_argument(
        "-p", "--prefix",
        type=str,
        default="sk",
        help="Prefix for the keys (default: 'sk')"
    )
    
    parser.add_argument(
        "--no-prefix",
        action="store_true",
        help="Generate keys without prefix"
    )
    
    parser.add_argument(
        "--env",
        action="store_true",
        help="Output in environment variable format"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.count < 1:
        print("Error: Count must be at least 1", file=sys.stderr)
        sys.exit(1)
    
    if args.length < 8:
        print("Error: Length must be at least 8 bytes", file=sys.stderr)
        sys.exit(1)
    
    # Set prefix
    prefix = "" if args.no_prefix else args.prefix
    
    # Generate keys
    if args.count == 1:
        key = generate_api_key(args.length, prefix)
        if args.env:
            print(f"API_KEY={key}")
        else:
            print(f"Generated API key: {key}")
    else:
        keys = generate_multiple_keys(args.count, args.length, prefix)
        if args.env:
            print(f"API_KEY={keys[0]}")
            if len(keys) > 1:
                additional_keys = ",".join(keys[1:])
                print(f"ADDITIONAL_API_KEYS={additional_keys}")
        else:
            print(f"Generated {args.count} API keys:")
            for i, key in enumerate(keys, 1):
                print(f"  {i}: {key}")
            
            print("\nEnvironment variable format:")
            print(f"API_KEY={keys[0]}")
            if len(keys) > 1:
                additional_keys = ",".join(keys[1:])
                print(f"ADDITIONAL_API_KEYS={additional_keys}")
    
    # Security reminder
    if not args.env:
        print("\n" + "="*60)
        print("SECURITY REMINDERS:")
        print("- Store these keys securely")
        print("- Never commit them to version control")
        print("- Use environment variables or secret managers")
        print("- Rotate keys regularly")
        print("- Each client should have a unique key")
        print("="*60)

if __name__ == "__main__":
    main() 