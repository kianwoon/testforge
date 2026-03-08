# bot/bot/test_case_parser.py
import re
from typing import List
from .models import TestCaseSpec

class TestCaseParser:
    def __init__(self):
        # Patterns for structured test case
        self.patterns = {
            'name': r'Test:\s*(.+?)(?=\n|$)',
            'scope': r'Scope:\s*(.+?)(?=\n|$)',
            'priority': r'Priority:\s*(P[0-2])',
        }

    async def parse(self, text: str) -> TestCaseSpec:
        # Extract name
        name_match = re.search(self.patterns['name'], text, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else "Unnamed Test"

        # Extract scope
        scope_match = re.search(self.patterns['scope'], text, re.IGNORECASE)
        scope = scope_match.group(1).strip() if scope_match else "General"

        # Extract priority
        priority_match = re.search(self.patterns['priority'], text, re.IGNORECASE)
        priority = priority_match.group(1) if priority_match else "P1"

        # Extract specs (bullet points after "Specs:")
        specs = self._extract_bullet_points(text, 'specs')

        # Extract steps (numbered or bulleted after "Steps:")
        steps = self._extract_steps(text)

        return TestCaseSpec(
            name=name,
            scope=scope,
            specs=specs,
            steps=steps,
            priority=priority
        )

    def _extract_bullet_points(self, text: str, section: str) -> List[str]:
        lines = text.split('\n')
        in_section = False
        bullets = []

        for line in lines:
            line_lower = line.lower().strip()
            if line_lower.startswith(f'{section}:'):
                in_section = True
                continue

            if in_section:
                if line.strip() == '':
                    continue
                if line.startswith('-') or line.startswith('*'):
                    bullets.append(line.lstrip('-*').strip())
                elif line[0].isdigit() and '.' in line[:3]:
                    continue
                elif not line.startswith(' '):
                    break

        return bullets

    def _extract_steps(self, text: str) -> List[str]:
        lines = text.split('\n')
        in_steps = False
        steps = []

        for line in lines:
            line_lower = line.lower().strip()
            if line_lower.startswith('steps:'):
                in_steps = True
                continue

            if in_steps:
                if line.strip() == '':
                    continue

                numbered_match = re.match(r'^\d+[\.)]\s*(.+)', line.strip())
                if numbered_match:
                    steps.append(numbered_match.group(1))
                elif line.startswith('-') or line.startswith('*'):
                    steps.append(line.lstrip('-*').strip())
                elif not line.startswith(' '):
                    break

        if not steps:
            steps_match = re.search(r'Steps:\s*\n((?:.+\n)+)', text, re.IGNORECASE)
            if steps_match:
                steps_text = steps_match.group(1)
                steps = [s.strip() for s in steps_text.split('\n') if s.strip()]

        return steps
