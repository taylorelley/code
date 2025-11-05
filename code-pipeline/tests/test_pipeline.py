"""
Tests for Code Pipeline

These tests verify the pipeline functionality without requiring
a running Code binary (mocked).
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.code_pipeline import Pipeline


class TestPipeline:
    """Test suite for Code Pipeline"""

    def test_pipeline_initialization(self):
        """Test pipeline can be initialized"""
        pipeline = Pipeline()

        assert pipeline.type == "pipe"
        assert pipeline.id == "code_pipeline"
        assert pipeline.name == "Code Agentic Assistant"
        assert pipeline.valves is not None

    def test_valves_configuration(self):
        """Test pipeline valves (configuration)"""
        pipeline = Pipeline()

        # Check default values
        assert pipeline.valves.ENABLE_BROWSER == True
        assert pipeline.valves.ENABLE_AUTO_DRIVE == True
        assert pipeline.valves.MAX_CONCURRENT_SESSIONS == 10
        assert pipeline.valves.APPROVAL_POLICY == "on-request"
        assert pipeline.valves.SANDBOX_MODE == "workspace-write"

    @pytest.mark.asyncio
    async def test_on_startup(self):
        """Test pipeline startup"""
        pipeline = Pipeline()

        # Should not raise
        await pipeline.on_startup()

    @pytest.mark.asyncio
    async def test_on_shutdown(self):
        """Test pipeline shutdown"""
        pipeline = Pipeline()

        # Should not raise
        await pipeline.on_shutdown()

    @pytest.mark.asyncio
    async def test_empty_message_handling(self):
        """Test handling of empty messages"""
        pipeline = Pipeline()

        body = {"messages": []}

        # Collect response from async generator
        result = []
        async for chunk in pipeline.pipe(body):
            result.append(chunk)
        result = "".join(result)

        assert "Error" in result
        assert "No messages" in result

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test /help command"""
        pipeline = Pipeline()

        # Mock session creation to avoid needing Code binary
        with patch.object(pipeline, '_get_or_create_session', new_callable=AsyncMock) as mock_session:
            mock_session.return_value = {
                "manager": AsyncMock(),
                "translator": Mock(),
                "conversation_id": "test-conv-123",
                "user_id": "test-user",
                "working_dir": "/tmp/test"
            }

            body = {
                "messages": [
                    {"role": "user", "content": "/help"}
                ]
            }
            user = {"id": "test-user"}

            # Get response
            response = []
            async for chunk in pipeline.pipe(body, __user__=user):
                response.append(chunk)

            # Join response
            full_response = "".join(response)

            # Should contain help text
            assert "Available Commands" in full_response
            assert "/plan" in full_response
            assert "/solve" in full_response
            assert "/code" in full_response


class TestPipelineIntegration:
    """Integration tests (require Code binary)"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_conversation(self):
        """Test real conversation with Code binary (if available)"""
        pipeline = Pipeline()

        try:
            await pipeline.on_startup()

            body = {
                "messages": [
                    {"role": "user", "content": "Hello, what is 2+2?"}
                ]
            }
            user = {"id": "test-user"}

            # Collect response
            response = []
            async for chunk in pipeline.pipe(body, __user__=user):
                response.append(chunk)
                # Limit to prevent infinite loops
                if len(response) > 100:
                    break

            # Should get some response
            assert len(response) > 0

        except RuntimeError as e:
            # Code binary not available - skip test
            if "not found" in str(e):
                pytest.skip("Code binary not available")
            raise
        finally:
            await pipeline.on_shutdown()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
