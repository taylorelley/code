"""
Code Pipeline for Open WebUI

This pipeline integrates the Code agentic coding assistant into Open WebUI.
Provides all Code features through a web interface.
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import os


class Pipeline:
    class Valves(BaseModel):
        CODE_BINARY_PATH: str = os.getenv("CODE_BINARY_PATH", "code")
        ENABLE_BROWSER: bool = True
        ENABLE_AUTO_DRIVE: bool = True
        MAX_CONCURRENT_SESSIONS: int = 10
        DEFAULT_WORKING_DIR: str = os.getenv("CODE_WORKING_DIR", "/tmp/code-workspace")
        APPROVAL_POLICY: str = "on-request"
        SANDBOX_MODE: str = "workspace-write"
        MODEL: str = "gpt-4"

    def __init__(self):
        self.type = "manifold"
        self.name = "Code Pipeline"
        self.valves = self.Valves()

    def pipes(self) -> List[dict]:
        return [
            {
                "id": "code-pipeline",
                "name": "Code Pipeline"
            }
        ]

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        # This is a manifold pipeline that routes to the code-pipeline service
        # Open WebUI will send requests to http://code-pipeline:9099/v1/chat/completions
        return {"status": "routing to code-pipeline service"}
