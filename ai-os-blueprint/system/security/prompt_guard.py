import re

class PromptGuard:
    """
    A service to detect and block potential prompt injection attacks.
    This MVP uses a simple heuristic-based approach with a denylist of
    keywords and regular expression patterns.
    """

    def __init__(self):
        """Initializes the guard with a set of detection rules."""
        # Simple keyword-based detection
        self.denied_keywords = [
            "ignore all previous instructions",
            "ignore the above",
            "forget what you were doing",
            "your system prompt",
            "your initial prompt",
            "what are your instructions",
            "what is your initial prompt",
            "what is your system prompt",
            "what are your rules"
        ]

        # Regex-based detection for more complex patterns
        self.denied_patterns = [
            # Detects phrases like "You are now a..." or "You are a..." to change persona
            re.compile(r"^\s*you are (now |a |an )", re.IGNORECASE),
            # Detects markdown separators used to create a fake context block
            re.compile(r"^\s*---+\s*$"),
            re.compile(r"^\s*###\s+new instructions", re.IGNORECASE)
        ]

    def scan(self, utterance):
        """
        Scans a user utterance for potential prompt injection.

        :param utterance: The user input string.
        :return: A dictionary with a "is_safe" boolean and an optional "reason".
        """
        lower_utterance = utterance.lower().strip()

        # Check for exact keyword matches
        for keyword in self.denied_keywords:
            if keyword in lower_utterance:
                return {
                    "is_safe": False,
                    "reason": f"Detected suspicious keyword: '{keyword}'"
                }

        # Check for regex pattern matches
        for pattern in self.denied_patterns:
            if pattern.search(utterance):
                return {
                    "is_safe": False,
                    "reason": f"Detected suspicious pattern: {pattern.pattern}"
                }

        # If no threats are detected, the prompt is considered safe.
        return {"is_safe": True}
