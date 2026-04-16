# passai/core/generator.py

import secrets
import string
import math
from typing import Tuple

class PasswordGenerator:
    """Generate secure passwords and calculate strength"""
    
    def __init__(self):
        self.lowercase = string.ascii_lowercase
        self.uppercase = string.ascii_uppercase
        self.digits = string.digits
        self.symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        self.ambiguous = "il1Lo0O"
    
    def generate(
        self,
        length: int = 16,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_symbols: bool = True,
        exclude_ambiguous: bool = False
    ) -> str:
        """Generate random password"""
        if length < 4:
            length = 4
        if length > 128:
            length = 128
        
        # Build character set
        charset = ""
        required_chars = []
        
        if use_lowercase:
            chars = self.lowercase
            if exclude_ambiguous:
                chars = "".join(c for c in chars if c not in self.ambiguous)
            charset += chars
            required_chars.append(secrets.choice(chars))
        
        if use_uppercase:
            chars = self.uppercase
            if exclude_ambiguous:
                chars = "".join(c for c in chars if c not in self.ambiguous)
            charset += chars
            required_chars.append(secrets.choice(chars))
        
        if use_digits:
            chars = self.digits
            if exclude_ambiguous:
                chars = "".join(c for c in chars if c not in self.ambiguous)
            charset += chars
            required_chars.append(secrets.choice(chars))
        
        if use_symbols:
            charset += self.symbols
            required_chars.append(secrets.choice(self.symbols))
        
        if not charset:
            charset = self.lowercase + self.uppercase + self.digits
            required_chars = [
                secrets.choice(self.lowercase),
                secrets.choice(self.uppercase),
                secrets.choice(self.digits)
            ]
        
        # Generate remaining characters
        remaining_length = length - len(required_chars)
        password_chars = required_chars + [
            secrets.choice(charset) for _ in range(remaining_length)
        ]
        
        # Shuffle
        password_list = list(password_chars)
        for i in range(len(password_list) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_list[i], password_list[j] = password_list[j], password_list[i]
        
        return "".join(password_list)
    
    def calculate_strength(self, password: str) -> Tuple[int, str]:
        """
        Calculate password strength
        Returns (score 0-100, description)
        """
        if not password:
            return 0, "Empty"
        
        length = len(password)
        
        # Character variety
        has_lower = any(c in self.lowercase for c in password)
        has_upper = any(c in self.uppercase for c in password)
        has_digit = any(c in self.digits for c in password)
        has_symbol = any(c in self.symbols for c in password)
        
        charset_size = 0
        if has_lower:
            charset_size += 26
        if has_upper:
            charset_size += 26
        if has_digit:
            charset_size += 10
        if has_symbol:
            charset_size += len(self.symbols)
        
        # Calculate entropy
        if charset_size > 0:
            entropy = length * math.log2(charset_size)
        else:
            entropy = 0
        
        # Score based on entropy
        # < 28 bits: very weak
        # 28-35: weak
        # 36-59: fair
        # 60-127: strong
        # >= 128: very strong
        
        if entropy < 28:
            score = int((entropy / 28) * 20)
            desc = "Very Weak"
        elif entropy < 36:
            score = 20 + int(((entropy - 28) / 8) * 20)
            desc = "Weak"
        elif entropy < 60:
            score = 40 + int(((entropy - 36) / 24) * 30)
            desc = "Fair"
        elif entropy < 128:
            score = 70 + int(((entropy - 60) / 68) * 20)
            desc = "Strong"
        else:
            score = 90 + min(10, int((entropy - 128) / 20))
            desc = "Very Strong"
        
        # Penalties
        if length < 8:
            score = min(score, 30)
        
        # Check for common patterns
        if self._has_common_patterns(password):
            score = max(0, score - 20)
            if score < 40:
                desc = "Weak (Pattern)"
        
        return min(100, max(0, score)), desc
    
    def _has_common_patterns(self, password: str) -> bool:
        """Check for common patterns"""
        pw_lower = password.lower()
        
        # Sequential characters
        sequences = ["abc", "bcd", "cde", "123", "234", "345", "678", "789"]
        for seq in sequences:
            if seq in pw_lower:
                return True
        
        # Repeated characters
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                return True
        
        # Common words
        common = ["password", "qwerty", "letmein", "admin", "welcome"]
        for word in common:
            if word in pw_lower:
                return True
        
        return False
    
    def check_reused(self, password: str, all_passwords: list) -> bool:
        """Check if password is reused"""
        return password in all_passwords
