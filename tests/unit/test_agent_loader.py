"""
Unit tests for configuration-driven Agent loader.
"""

from pathlib import Path

from src.application.agent_loader import load_agent_from_yaml, parse_agent_definition
from src.domain.agent import AgentState


def test_parse_agent_definition_dict() -> None:
    raw_data = {
        "agent": {
            "id": "agent_test",
            "name": "Test Agent",
            "role": "Tester",
            "description": "Performs unit testing",
            "responsibilities": ["run tests", "report bugs"],
            "capabilities": ["testing"],
            "model": {
                "provider": "groq",
                "model": "llama-3.3-70b-versatile",
                "temperature": 0.2,
            },
            "permissions": ["execute_tests"],
            "verification": {
                "required": True,
                "verifier_role": "QA Lead",
            },
        }
    }

    agent = parse_agent_definition(raw_data)
    assert agent.id == "agent_test"
    assert agent.name == "Test Agent"
    assert agent.role == "Tester"
    assert agent.current_state == AgentState.IDLE
    assert agent.model_configuration.provider == "groq"
    assert agent.model_configuration.temperature == 0.2
    assert agent.permission_profile.has_permission("execute_tests")
    assert agent.verification_policy.required is True


def test_load_agent_from_yaml_file(tmp_path: Path) -> None:
    yaml_file = tmp_path / "test_agent.yaml"
    yaml_file.write_text(
        """
agent:
  id: yaml_agent
  name: YAML Agent
  role: Analyst
  responsibilities:
    - Analyze data
  model:
    provider: groq
    model: llama-3.3-70b-versatile
""",
        encoding="utf-8",
    )

    agent = load_agent_from_yaml(yaml_file)
    assert agent.id == "yaml_agent"
    assert agent.name == "YAML Agent"
    assert agent.role == "Analyst"


def test_load_sample_researcher_agent_yaml() -> None:
    path = Path("config/agents/researcher.yaml")
    agent = load_agent_from_yaml(path)

    assert agent.id == "researcher_001"
    assert agent.name == "Technical Researcher"
    assert agent.role == "researcher"
    assert "technical_research" in agent.capabilities
