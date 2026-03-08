# bot/tests/test_parser.py
import pytest
from bot.test_case_parser import TestCaseParser

@pytest.mark.asyncio
async def test_parse_structured_test_case():
    parser = TestCaseParser()

    text = """
Test: Login with invalid credentials
Scope: Authentication Module
Specs:
- Verify error message appears
- Verify login button is disabled
Steps:
1. Navigate to /login
2. Enter invalid email
3. Enter invalid password
4. Click login button
"""

    test_case = await parser.parse(text)

    assert test_case.name == "Login with invalid credentials"
    assert test_case.scope == "Authentication Module"
    assert len(test_case.specs) == 2
    assert len(test_case.steps) == 4

@pytest.mark.asyncio
async def test_parse_handles_missing_optional_fields():
    parser = TestCaseParser()

    text = """
Test: Simple test
Scope: Test Module
Steps:
1. Step one
2. Step two
"""

    test_case = await parser.parse(text)

    assert test_case.name == "Simple test"
    assert test_case.specs == []
    assert test_case.priority == "P1"
