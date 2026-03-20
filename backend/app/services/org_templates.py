"""Pre-built Agent Org templates for the community feed.

Each template defines:
- name: human-readable label
- description: what the team does
- topology: graph of agents and their connections
- config: roles, memory setup, default processes
"""

from typing import Any

OrgTemplate = dict[str, Any]

CATEGORIES: dict[str, list[str]] = {
    "research": ["AutoResearch Team", "Science Discovery Team"],
    "engineering": ["Code Review Team", "DevOps Pipeline", "Data Pipeline"],
    "content": ["Content Creation"],
    "support": ["Customer Support"],
}

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
            "default_model": "anthropic/claude-sonnet-4-6",
            "memory_enabled": True,
            "max_concurrent": 2,
        },
    },
    # ------------------------------------------------------------------
    # DevOps Pipeline
    # ------------------------------------------------------------------
    {
        "name": "DevOps Pipeline",
        "description": (
            "An automated DevOps org covering CI/CD deployment, infrastructure "
            "monitoring, incident rollback, and real-time alerting."
        ),
        "topology": {
            "agents": [
                {
                    "role": "deployer",
                    "description": "Orchestrates build, test, and release pipelines.",
                    "model": "anthropic/claude-sonnet-4-6",
                    "connections": ["monitor"],
                },
                {
                    "role": "monitor",
                    "description": "Tracks health metrics, latency, and error rates post-deploy.",
                    "model": "anthropic/claude-haiku-4-5",
                    "connections": ["rollback", "alerter"],
                },
                {
                    "role": "rollback",
                    "description": "Reverts broken deployments to the last known-good state.",
                    "model": "anthropic/claude-sonnet-4-6",
                    "connections": [],
                },
                {
                    "role": "alerter",
                    "description": "Sends notifications to on-call channels when anomalies are detected.",
                    "model": "anthropic/claude-haiku-4-5",
                    "connections": [],
                },
            ],
            "connections": [
                {"from": "deployer", "to": "monitor", "label": "post-deploy"},
                {"from": "monitor", "to": "rollback", "label": "on-failure"},
                {"from": "monitor", "to": "alerter", "label": "alert"},
            ],
            "entry_point": "deployer",
            "exit_point": "alerter",
        },
        "config": {
            "default_model": "anthropic/claude-sonnet-4-6",
            "memory_enabled": True,
            "max_concurrent": 4,
            "memory": {"type": "shared", "backend": "pheromone"},
            "processes": {"max_iterations": 1, "output_format": "deployment_report"},
            "roles": {
                "deployer": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.1},
                "monitor": {"model": "anthropic/claude-haiku-4-5", "temperature": 0.1},
                "rollback": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.1},
                "alerter": {"model": "anthropic/claude-haiku-4-5", "temperature": 0.2},
            },
        },
    },
    # ------------------------------------------------------------------
    # Content Creation
    # ------------------------------------------------------------------
    {
        "name": "Content Creation",
        "description": (
            "A full content-lifecycle team: topic researcher, narrative writer, "
            "editorial reviewer, and multi-channel publisher."
        ),
        "topology": {
            "agents": [
                {
                    "role": "researcher",
                    "description": "Gathers topic background, trending angles, and audience insights.",
                    "model": "anthropic/claude-haiku-4-5",
                    "connections": ["writer"],
                },
                {
                    "role": "writer",
                    "description": "Drafts engaging long-form or short-form content from research.",
                    "model": "anthropic/claude-sonnet-4-6",
                    "connections": ["editor"],
                },
                {
                    "role": "editor",
                    "description": "Polishes copy for tone, grammar, SEO, and brand voice.",
                    "model": "anthropic/claude-sonnet-4-6",
                    "connections": ["publisher"],
                },
                {
                    "role": "publisher",
                    "description": "Formats and schedules content for the target channel.",
                    "model": "anthropic/claude-haiku-4-5",
                    "connections": [],
                },
            ],
            "connections": [
                {"from": "researcher", "to": "writer", "label": "brief"},
                {"from": "writer", "to": "editor", "label": "draft"},
                {"from": "editor", "to": "publisher", "label": "approved"},
            ],
            "entry_point": "researcher",
            "exit_point": "publisher",
        },
        "config": {
            "default_model": "anthropic/claude-sonnet-4-6",
            "memory_enabled": True,
            "max_concurrent": 2,
            "memory": {"type": "shared", "backend": "pheromone"},
            "processes": {"max_iterations": 2, "stop_condition": "publisher_approved"},
            "roles": {
                "researcher": {"model": "anthropic/claude-haiku-4-5", "temperature": 0.3},
                "writer": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.7},
                "editor": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.2},
                "publisher": {"model": "anthropic/claude-haiku-4-5", "temperature": 0.1},
            },
        },
    },
    # ------------------------------------------------------------------
    # Customer Support
    # ------------------------------------------------------------------
    {
        "name": "Customer Support",
        "description": (
            "An intelligent support pipeline that triages inbound requests, "
            "generates responses, escalates complex issues, and tracks analytics."
        ),
        "topology": {
            "agents": [
                {
                    "role": "triage",
                    "description": "Classifies tickets by urgency, category, and sentiment.",
                    "model": "anthropic/claude-haiku-4-5",
                    "connections": ["responder", "escalation"],
                },
                {
                    "role": "responder",
                    "description": "Drafts accurate, empathetic replies using knowledge base.",
                    "model": "anthropic/claude-sonnet-4-6",
                    "connections": ["analytics"],
                },
                {
                    "role": "escalation",
                    "description": "Routes high-severity issues to human agents with full context.",
                    "model": "anthropic/claude-sonnet-4-6",
                    "connections": ["analytics"],
                },
                {
                    "role": "analytics",
                    "description": "Aggregates resolution metrics and surfaces recurring issues.",
                    "model": "anthropic/claude-haiku-4-5",
                    "connections": [],
                },
            ],
            "connections": [
                {"from": "triage", "to": "responder", "label": "standard"},
                {"from": "triage", "to": "escalation", "label": "urgent"},
                {"from": "responder", "to": "analytics", "label": "resolved"},
                {"from": "escalation", "to": "analytics", "label": "escalated"},
            ],
            "entry_point": "triage",
            "exit_point": "analytics",
        },
        "config": {
            "default_model": "anthropic/claude-sonnet-4-6",
            "memory_enabled": True,
            "max_concurrent": 8,
            "memory": {"type": "shared", "backend": "pheromone"},
            "processes": {"max_iterations": 1, "output_format": "support_ticket"},
            "roles": {
                "triage": {"model": "anthropic/claude-haiku-4-5", "temperature": 0.1},
                "responder": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.4},
                "escalation": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.2},
                "analytics": {"model": "anthropic/claude-haiku-4-5", "temperature": 0.1},
            },
        },
    },
    # ------------------------------------------------------------------
    # Data Pipeline
    # ------------------------------------------------------------------
    {
        "name": "Data Pipeline",
        "description": (
            "An end-to-end data processing org: ingests raw sources, transforms "
            "and normalises records, validates quality, and publishes clean datasets."
        ),
        "topology": {
            "agents": [
                {
                    "role": "ingester",
                    "description": "Pulls data from APIs, files, or streams and stages it.",
                    "model": "anthropic/claude-haiku-4-5",
                    "connections": ["transformer"],
                },
                {
                    "role": "transformer",
                    "description": "Applies cleaning, enrichment, and schema normalisation.",
                    "model": "anthropic/claude-sonnet-4-6",
                    "connections": ["validator"],
                },
                {
                    "role": "validator",
                    "description": "Runs data-quality checks and flags anomalies for review.",
                    "model": "anthropic/claude-sonnet-4-6",
                    "connections": ["publisher"],
                },
                {
                    "role": "publisher",
                    "description": "Writes validated records to the target data store or warehouse.",
                    "model": "anthropic/claude-haiku-4-5",
                    "connections": [],
                },
            ],
            "connections": [
                {"from": "ingester", "to": "transformer", "label": "raw"},
                {"from": "transformer", "to": "validator", "label": "normalised"},
                {"from": "validator", "to": "publisher", "label": "clean"},
            ],
            "entry_point": "ingester",
            "exit_point": "publisher",
        },
        "config": {
            "default_model": "anthropic/claude-sonnet-4-6",
            "memory_enabled": False,
            "max_concurrent": 4,
            "memory": {"type": "none"},
            "processes": {"max_iterations": 1, "output_format": "dataset"},
            "roles": {
                "ingester": {"model": "anthropic/claude-haiku-4-5", "temperature": 0.1},
                "transformer": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.2},
                "validator": {"model": "anthropic/claude-sonnet-4-6", "temperature": 0.1},
                "publisher": {"model": "anthropic/claude-haiku-4-5", "temperature": 0.1},
            },
        },
    },
]

# Back-fill the 3 original templates with unified config keys so they all
# expose `default_model`, `memory_enabled`, and `max_concurrent`.
_ORIGINAL_DEFAULTS: dict[str, dict] = {
    "AutoResearch Team": {"default_model": "anthropic/claude-sonnet-4-6", "memory_enabled": True, "max_concurrent": 2},
    "Code Review Team": {"default_model": "anthropic/claude-sonnet-4-6", "memory_enabled": True, "max_concurrent": 5},
    "Science Discovery Team": {"default_model": "anthropic/claude-sonnet-4-6", "memory_enabled": True, "max_concurrent": 2},
}

for _t in TEMPLATES:
    if _t["name"] in _ORIGINAL_DEFAULTS:
        _defaults = _ORIGINAL_DEFAULTS[_t["name"]]
        for _k, _v in _defaults.items():
            _t["config"].setdefault(_k, _v)
        # Also ensure topology has a `connections` list
        _t["topology"].setdefault("connections", [])
        # Ensure each agent has a `connections` key mirroring connects_to
        for _agent in _t["topology"].get("agents", []):
            if "connections" not in _agent:
                _agent["connections"] = _agent.get("connects_to", [])
            if "model" not in _agent:
                roles_config = _t["config"].get("roles", {})
                role_cfg = roles_config.get(_agent["role"], {})
                _agent["model"] = role_cfg.get("model", _defaults["default_model"])


def get_all_templates() -> list[OrgTemplate]:
    """Return all built-in org templates."""
    return TEMPLATES


def get_template_by_name(name: str) -> OrgTemplate | None:
    """Return a single template by exact name, or None."""
    for t in TEMPLATES:
        if t["name"] == name:
            return t
    return None
