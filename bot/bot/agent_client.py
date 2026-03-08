# bot/bot/agent_client.py
import aiohttp
from typing import Dict, Any, Optional
from .models import TestCaseSpec


class AgentAPIClient:
    """Async HTTP client to communicate with Agent API."""

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the Agent API client.

        Args:
            base_url: Base URL of the Agent API (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def submit_test_case(self, test_case: TestCaseSpec) -> str:
        """
        Submit a test case to the Agent for script generation.

        Args:
            test_case: TestCaseSpec object containing test details

        Returns:
            job_id: Unique identifier for the submitted job

        Raises:
            Exception: If the API returns a non-200 status code
        """
        url = f"{self.base_url}/api/v1/submit"
        payload = test_case.model_dump()

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Agent returned {response.status}: {error_text}")
                data = await response.json()
                return data["job_id"]

    async def get_status(self, job_id: str) -> Dict[str, Any]:
        """
        Query the status of a submitted job.

        Args:
            job_id: Unique identifier for the job

        Returns:
            Dictionary containing job status information

        Raises:
            Exception: If job is not found (404) or API error occurs
        """
        url = f"{self.base_url}/api/v1/status/{job_id}"

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url) as response:
                if response.status == 404:
                    raise Exception(f"Job {job_id} not found")
                elif response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Agent returned {response.status}: {error_text}")
                return await response.json()

    async def get_generated_script(self, job_id: str) -> Optional[str]:
        """
        Retrieve the generated test script for a completed job.

        Args:
            job_id: Unique identifier for the job

        Returns:
            Generated script as string if job is completed, None otherwise
        """
        status = await self.get_status(job_id)
        if status["status"] == "completed":
            # TODO: Implement actual script retrieval when Agent API provides it
            # For now, return a placeholder
            return f"# Script for job {job_id}"
        return None
