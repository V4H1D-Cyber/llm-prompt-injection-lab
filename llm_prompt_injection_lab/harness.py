"""
harness.py
-----------
Runs every attack in attacks.py against both the VulnerableAssistant and
the HardenedAssistant, and writes a results table to results.md (+ raw
JSON to results.json) so results are versioned alongside the code.

Usage:
    python -m llm_prompt_injection_lab.harness
"""

import json
from pathlib import Path

from .assistant import VulnerableAssistant, HardenedAssistant
from .attacks import ATTACKS
from .backends import MockBackend

SECRET_API_KEY = "sk-lab-DEMO-1234567890"  # fake key, used only to detect leakage


def run() -> list[dict]:
    backend = MockBackend(secret_api_key=SECRET_API_KEY)
    vulnerable = VulnerableAssistant(backend)
    hardened = HardenedAssistant(backend, secret_api_key=SECRET_API_KEY)

    rows = []
    for attack in ATTACKS:
        v = vulnerable.answer(attack.user_message)
        h = hardened.answer(attack.user_message)
        rows.append({
            "id": attack.id,
            "name": attack.name,
            "owasp": attack.owasp,
            "payload": attack.user_message,
            "vulnerable_leaked": v.leaked_secret,
            "vulnerable_response": v.text,
            "hardened_leaked": h.leaked_secret,
            "hardened_response": h.text,
            "hardened_flags": h.filter_flags,
        })
    return rows


def render_markdown(rows: list[dict]) -> str:
    lines = [
        "# Results\n",
        f"Ran {len(rows)} attack techniques against both assistants.\n",
        "| # | Technique | OWASP | Vulnerable build | Hardened build |",
        "|---|-----------|-------|:---:|:---:|",
    ]
    for r in rows:
        v = "LEAKED" if r["vulnerable_leaked"] else "blocked"
        h = "LEAKED" if r["hardened_leaked"] else "blocked"
        lines.append(f"| {r['id']} | {r['name']} | {r['owasp']} | {v} | {h} |")

    v_leaks = sum(1 for r in rows if r["vulnerable_leaked"])
    h_leaks = sum(1 for r in rows if r["hardened_leaked"])
    lines.append("")
    lines.append(f"**Vulnerable build: {v_leaks}/{len(rows)} attacks succeeded.**")
    lines.append(f"**Hardened build: {h_leaks}/{len(rows)} attacks succeeded.**")
    lines.append("")
    lines.append("## Per-attack detail\n")
    for r in rows:
        lines.append(f"### {r['id']}: {r['name']} ({r['owasp']})")
        lines.append(f"- Payload: `{r['payload']}`")
        lines.append(f"- Vulnerable build response: `{r['vulnerable_response']}`")
        lines.append(f"- Hardened build response: `{r['hardened_response']}`")
        if r["hardened_flags"]:
            lines.append(f"- Hardened build filter log: {r['hardened_flags']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    rows = run()
    out_dir = Path(__file__).resolve().parent.parent
    (out_dir / "results.json").write_text(json.dumps(rows, indent=2))
    (out_dir / "results.md").write_text(render_markdown(rows))
    print(render_markdown(rows))
