#!/usr/bin/env python3
"""
Test file to demonstrate AI coding capabilities
Created with Ollama qwen2.5-coder:7b and MCP servers
"""

def hello_world():
    """Simple hello world function"""
    print("Hello from AI-powered coding!")

def fibonacci(n):
    """Calculate fibonacci sequence up to n terms"""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_sequence = [0, 1]
    for i in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence

def reverse_string(text):
    """Reverse a string"""
    return text[::-1]

def is_palindrome(text):
    """Check if a string is a palindrome"""
    cleaned = ''.join(c.lower() for c in text if c.isalnum())
    return cleaned == cleaned[::-1]

if __name__ == "__main__":
    print("=== AI Coding Test ===\n")
    
    # Test hello world
    hello_world()
    
    # Test fibonacci
    print(f"\nFibonacci(10): {fibonacci(10)}")
    
    # Test string operations
    test_string = "Hello AI"
    print(f"\nOriginal: {test_string}")
    print(f"Reversed: {reverse_string(test_string)}")
    
    # Test palindrome
    palindrome_test = "A man a plan a canal Panama"
    print(f"\nIs '{palindrome_test}' a palindrome? {is_palindrome(palindrome_test)}")
    
    print("\n=== All tests completed! ===")
