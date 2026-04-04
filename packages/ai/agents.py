"""
CrewAI Agent Definitions — 3 specialized AI agents for team optimization.
"""

import os

# LLM Configuration
GEMINI_MODEL = "gemini-2.0-flash-exp"
CLAUDE_MODEL = "claude-haiku-4"


def get_budget_optimizer_config():
    """Agent 1: Budget Optimizer (Gemini — FREE)."""
    return {
        "role": "Budget Optimizer",
        "goal": "Maximize predicted fantasy points within ₹100 budget while respecting role constraints",
        "backstory": (
            "You are an expert in combinatorial optimization and integer linear programming. "
            "You've optimized thousands of fantasy teams and understand the mathematics of budget allocation. "
            "You use Google OR-Tools to solve the ILP problem for maximum points within budget."
        ),
        "llm_model": GEMINI_MODEL,
        "tools": ["budget_optimizer_tool"],
        "verbose": True,
    }


def get_differential_expert_config():
    """Agent 2: Differential Expert (Gemini — FREE)."""
    return {
        "role": "Differential Expert",
        "goal": "Identify 2-3 low-ownership, high-upside players that differentiate the team",
        "backstory": (
            "You are a contrarian analyst who finds hidden gems. You study ownership patterns "
            "and player performance variance to identify undervalued options. You use RAG to query "
            "historical data on differential success rates."
        ),
        "llm_model": GEMINI_MODEL,
        "tools": ["rag_query_tool", "ownership_predictor_tool"],
        "verbose": True,
    }


def get_risk_manager_config():
    """Agent 3: Risk Manager (Claude — complex reasoning)."""
    return {
        "role": "Risk Manager",
        "goal": "Balance team risk/reward profile based on user's risk tolerance",
        "backstory": (
            "You are a portfolio strategist who applies financial risk management principles "
            "to fantasy sports. You understand variance, correlation, and risk-adjusted returns. "
            "You use Monte Carlo simulation (1000 iterations) to assess outcome distributions."
        ),
        "llm_model": CLAUDE_MODEL,
        "tools": ["monte_carlo_tool", "variance_calculator_tool"],
        "verbose": True,
    }
