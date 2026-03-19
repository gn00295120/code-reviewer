"""Pre-built Agent Org templates for the community feed.

Each template defines:
- name: human-readable label
- description: what the team does
- topology: graph of agents and their connections
- config: roles, memory setup, default processes
"""

from typing import Any

OrgTemplate = dict[str, Any]

TEMPLATES: list[OrgTemplate] = [
    {
        "name": "AutoResearch Team",
        "description": (
            "A self-organizing research collective that takes a topic, gathers "
            "evidence, synthesises findings, and delivers a polished report."
        ),
        "topology": {
            "agents": [
                {
                    "role": "researcher",
                    "description": "Collects sources, papers, and raw data on the topic.",
                    "connects_to": ["analyst"],
                },
                {
                    "role": "analyst",
                    "description": "Evaluates evidence quality and extracts key insights.",
                    "connects_to": ["writer"],
                },
                {
                    "role": "writer",
                    "description": "Structures insights into a coherent narrative draft.",
                    "connects_to": ["reviewer"],
                },
                {
                    "role": "reviewer",
                    "description": "Critiques the draft for accuracy, clarity, and completeness.",
                    "connects_to": ["writer"],
                },
            ],
            "entry_point": "researcher",
            "exit_point": "reviewer",
        },
        "config": {
            "memory": {
                "type": "shared",
                "backend": "pheromone",
            },
            "processes": {
                "max_iterations": 3,
                "stop_condition": "reviewer_approved",
            },
            "roles": {
                "researcher": {"model": "anthropic/claude-haiku-4-5", "temperature": 0.3},
                "analyst": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.2},
                "writer": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.7},
                "reviewer": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.1},
            },
        },
    },
    {
        "name": "Code Review Team",
        "description": (
            "A specialised multi-agent code review squad covering logic correctness, "
            "security vulnerabilities, edge-case handling, coding conventions, and "
            "runtime performance."
        ),
        "topology": {
            "agents": [
                {
                    "role": "logic",
                    "description": "Verifies algorithmic correctness and control flow.",
                    "connects_to": ["security", "edge_case"],
                },
                {
                    "role": "security",
                    "description": "Identifies injection risks, auth flaws, and data leaks.",
                    "connects_to": ["convention"],
                },
                {
                    "role": "edge_case",
                    "description": "Explores boundary conditions and failure modes.",
                    "connects_to": ["convention"],
                },
                {
                    "role": "convention",
                    "description": "Enforces style guidelines and naming standards.",
                    "connects_to": ["performance"],
                },
                {
                    "role": "performance",
                    "description": "Spots algorithmic inefficiencies and resource waste.",
                    "connects_to": [],
                },
            ],
            "entry_point": "logic",
            "exit_point": "performance",
            "parallel_groups": [["security", "edge_case"]],
        },
        "config": {
            "memory": {
                "type": "shared",
                "backend": "pheromone",
            },
            "processes": {
                "max_iterations": 1,
                "output_format": "review_findings",
            },
            "roles": {
                "logic": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.1},
                "security": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.1},
                "edge_case": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.2},
                "convention": {"model": "anthropic/claude-haiku-4-5", "temperature": 0.1},
                "performance": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.1},
            },
        },
    },
    {
        "name": "Science Discovery Team",
        "description": (
            "An end-to-end scientific-method pipeline: forms hypotheses, designs "
            "experiments, analyses results, and drafts publication-ready summaries."
        ),
        "topology": {
            "agents": [
                {
                    "role": "hypothesis",
                    "description": "Generates and ranks candidate hypotheses from background knowledge.",
                    "connects_to": ["experiment"],
                },
                {
                    "role": "experiment",
                    "description": "Designs experimental protocols or simulation plans to test hypotheses.",
                    "connects_to": ["analysis"],
                },
                {
                    "role": "analysis",
                    "description": "Interprets results, computes statistics, and draws conclusions.",
                    "connects_to": ["publication"],
                },
                {
                    "role": "publication",
                    "description": "Writes structured abstract, methods, results, and discussion sections.",
                    "connects_to": [],
                },
            ],
            "entry_point": "hypothesis",
            "exit_point": "publication",
        },
        "config": {
            "memory": {
                "type": "shared",
                "backend": "pheromone",
            },
            "processes": {
                "max_iterations": 2,
                "stop_condition": "publication_ready",
                "citation_style": "APA",
            },
            "roles": {
                "hypothesis": {"model": "anthropic/claude-opus-4-6", "temperature": 0.5},
                "experiment": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.3},
                "analysis": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.2},
                "publication": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.6},
            },
        },
    },
]


def get_all_templates() -> list[OrgTemplate]:
    """Return all built-in org templates."""
    return TEMPLATES


def get_template_by_name(name: str) -> OrgTemplate | None:
    """Return a single template by exact name, or None."""
    for t in TEMPLATES:
        if t["name"] == name:
            return t
    return None
