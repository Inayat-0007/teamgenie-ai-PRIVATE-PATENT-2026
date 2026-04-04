"""
CrewAI Agent Definitions — 3 specialized AI agents for team optimization.
Configurable via environment variables for model rotation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Final

# ---------------------------------------------------------------------------
# LLM Configuration (override via env for A/B testing or cost control)
# ---------------------------------------------------------------------------
PRIMARY_LLM: Final[str] = os.getenv("PRIMARY_LLM", "gemini-2.0-flash")
FALLBACK_LLM: Final[str] = os.getenv("FALLBACK_LLM", "deepseek-v3")
REASONING_LLM: Final[str] = os.getenv("REASONING_LLM", "claude-haiku-4")


@dataclass(frozen=True)
class AgentConfig:
    """Immutable configuration for a CrewAI agent."""
    role: str
    goal: str
    backstory: str
    llm_model: str
    tools: tuple[str, ...] = ()
    max_iterations: int = 5
    temperature: float = 0.3
    verbose: bool = True
    allow_delegation: bool = False


def get_budget_optimizer_config() -> AgentConfig:
    """Agent 1: Budget Optimizer (Gemini — FREE tier)."""
    return AgentConfig(
        role="Budget Optimizer",
        goal=(
            "Maximize predicted fantasy points within ₹100 budget "
            "while satisfying cricket role constraints "
            "(min 3 BAT, 3 BOWL, 1 WK, 1 AR; max 7 from one team)"
        ),
        backstory=(
            "You are an expert in combinatorial optimization and integer linear programming. "
            "You've optimized thousands of fantasy teams and understand the mathematics of budget allocation. "
            "You use Google OR-Tools to solve the ILP problem for maximum points within budget. "
            "You never exceed the ₹100 salary cap under any circumstances."
        ),
        llm_model=PRIMARY_LLM,
        tools=("budget_optimizer_tool",),
        temperature=0.1,  # Deterministic for math
    )


def get_differential_expert_config() -> AgentConfig:
    """Agent 2: Differential Expert (Gemini — FREE tier)."""
    return AgentConfig(
        role="Differential Expert",
        goal="Identify 2-3 low-ownership, high-upside players that differentiate the team from competitors",
        backstory=(
            "You are a contrarian analyst who finds hidden gems. You study ownership patterns "
            "and player performance variance to identify undervalued options. You use RAG to query "
            "historical data on differential success rates. Players under 25% ownership with "
            "above-average predicted points are your sweet spot."
        ),
        llm_model=PRIMARY_LLM,
        tools=("rag_query_tool", "ownership_predictor_tool"),
        temperature=0.5,  # Slightly creative
    )


def get_risk_manager_config() -> AgentConfig:
    """Agent 3: Risk Manager (Claude — complex reasoning)."""
    return AgentConfig(
        role="Risk Manager",
        goal="Balance team risk/reward profile based on user's risk tolerance and portfolio theory",
        backstory=(
            "You are a portfolio strategist who applies financial risk management principles "
            "to fantasy sports. You understand variance, correlation, and risk-adjusted returns. "
            "You use Monte Carlo simulation (1000 iterations) to assess outcome distributions. "
            "For safe profiles, minimize variance. For aggressive, maximize upside at the cost of floor."
        ),
        llm_model=REASONING_LLM,
        tools=("monte_carlo_tool", "variance_calculator_tool"),
        temperature=0.2,  # Precise reasoning
    )


def get_all_agents() -> dict[str, AgentConfig]:
    """Return all agent configs keyed by role slug."""
    return {
        "budget_optimizer": get_budget_optimizer_config(),
        "differential_expert": get_differential_expert_config(),
        "risk_manager": get_risk_manager_config(),
    }
