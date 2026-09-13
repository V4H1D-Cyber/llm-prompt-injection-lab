"""
Regression tests: every attack in attacks.py must succeed against the
vulnerable build (proves the harness models a real vulnerability, not a
strawman) and must be blocked by the hardened build (proves the defenses
actually work, and catches regressions if someone edits assistant.py later).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm_prompt_injection_lab.assistant import VulnerableAssistant, HardenedAssistant
from llm_prompt_injection_lab.attacks import ATTACKS
from llm_prompt_injection_lab.backends import MockBackend

SECRET_API_KEY = "sk-lab-DEMO-1234567890"


def _assistants():
    backend = MockBackend(secret_api_key=SECRET_API_KEY)
    return VulnerableAssistant(backend), HardenedAssistant(backend, secret_api_key=SECRET_API_KEY)


def test_every_attack_succeeds_against_vulnerable_build():
    vulnerable, _ = _assistants()
    for attack in ATTACKS:
        response = vulnerable.answer(attack.user_message)
        assert response.leaked_secret, f"{attack.id} ({attack.name}) unexpectedly failed to breach the vulnerable build"


def test_every_attack_is_blocked_by_hardened_build():
    _, hardened = _assistants()
    for attack in ATTACKS:
        response = hardened.answer(attack.user_message)
        assert not response.leaked_secret, f"{attack.id} ({attack.name}) breached the hardened build -- regression!"
        assert SECRET_API_KEY not in response.text


def test_hardened_build_still_answers_legitimate_questions():
    _, hardened = _assistants()
    response = hardened.answer("What are your support hours?")
    assert not response.leaked_secret
    assert "I can help" in response.text
