import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CodeReview(Base):
    __tablename__ = "code_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pr_url = Column(String(512), nullable=False)
    repo_name = Column(String(256), nullable=False)
    pr_number = Column(Integer, nullable=True)
    status = Column(
        Enum("pending", "running", "completed", "failed", "cancelled", name="review_status"),
        default="pending",
        nullable=False,
    )
    total_issues = Column(Integer, default=0)
    total_cost_usd = Column(Numeric(10, 6), default=0)
    config = Column(JSONB, default=dict)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    findings = relationship("ReviewFinding", back_populates="review", cascade="all, delete-orphan")


class ReviewFinding(Base):
    __tablename__ = "review_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id", ondelete="CASCADE"), nullable=False)
    agent_role = Column(String(64), nullable=False)
    severity = Column(
        Enum("high", "medium", "low", "info", name="finding_severity"),
        nullable=False,
    )
    file_path = Column(String(512), nullable=False)
    line_number = Column(Integer, nullable=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Numeric(10, 6), default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    review = relationship("CodeReview", back_populates="findings")


class ReviewTemplate(Base):
    __tablename__ = "review_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    rules = Column(JSONB, default=dict)
    created_by = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# World Model Sandbox
# ---------------------------------------------------------------------------


class WorldModel(Base):
    __tablename__ = "world_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    mujoco_xml = Column(Text, nullable=True)  # MuJoCo MJCF model definition
    model_type = Column(String(64), default="custom")  # crazyflie, jaco, ur5, custom
    current_state = Column(JSONB, default=dict)
    agent_config = Column(JSONB, default=dict)  # LLM agent configuration
    total_steps = Column(Integer, default=0)
    total_cost_usd = Column(Numeric(10, 6), default=0)
    status = Column(
        Enum("idle", "running", "paused", "completed", "error", name="world_model_status"),
        default="idle",
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("PhysicsEvent", back_populates="model", cascade="all, delete-orphan")


class PhysicsEvent(Base):
    __tablename__ = "physics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(
        UUID(as_uuid=True),
        ForeignKey("world_models.id", ondelete="CASCADE"),
        nullable=False,
    )
    step = Column(Integer, nullable=False)
    action = Column(JSONB, default=dict)  # Agent's command
    observation = Column(JSONB, default=dict)  # Sensor feedback
    reward = Column(Float, default=0.0)
    agent_reasoning = Column(Text, nullable=True)  # LLM reasoning trace
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Numeric(10, 6), default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    model = relationship("WorldModel", back_populates="events")


# ---------------------------------------------------------------------------
# Agent Community Feed
# ---------------------------------------------------------------------------


class AgentOrg(Base):
    __tablename__ = "agent_orgs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    topology = Column(JSONB, default=dict)  # Agent team structure
    config = Column(JSONB, default=dict)  # Roles, memory, processes
    is_template = Column(Boolean, default=False)  # Org code template
    fork_count = Column(Integer, default=0)
    forked_from_id = Column(UUID(as_uuid=True), ForeignKey("agent_orgs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = relationship("AgentPost", back_populates="org", cascade="all, delete-orphan")


class AgentPost(Base):
    __tablename__ = "agent_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("agent_orgs.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(128), nullable=False)  # Which agent in the org posted
    content_type = Column(String(64), default="text")  # text, review, model, experience
    content = Column(JSONB, default=dict)
    pheromone_state = Column(JSONB, default=dict)  # Stigmergy shared state snapshot
    likes = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    org = relationship("AgentOrg", back_populates="posts")
    replies = relationship("AgentPostReply", back_populates="post", cascade="all, delete-orphan")


class AgentPostReply(Base):
    __tablename__ = "agent_post_replies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("agent_posts.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("agent_orgs.id"), nullable=False)
    agent_name = Column(String(128), nullable=False)
    content = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("AgentPost", back_populates="replies")


class OrgFollow(Base):
    __tablename__ = "org_follows"

    follower_org_id = Column(UUID(as_uuid=True), ForeignKey("agent_orgs.id", ondelete="CASCADE"), primary_key=True)
    followed_org_id = Column(UUID(as_uuid=True), ForeignKey("agent_orgs.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PheromoneTrail(Base):
    __tablename__ = "pheromone_trails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("agent_orgs.id", ondelete="CASCADE"), nullable=False)
    shared_state = Column(JSONB, default=dict)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Historical Replay
# ---------------------------------------------------------------------------


class ReviewEvent(Base):
    __tablename__ = "review_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(64), nullable=False)  # review:started, review:agent:started, etc.
    event_data = Column(JSONB, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# v2.0 — Memory Palace
# ---------------------------------------------------------------------------


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_role = Column(String(64), nullable=False)  # logic, security, etc.
    memory_type = Column(String(64), nullable=False)  # pattern, learning, preference
    content = Column(JSONB, default=dict)  # The memory content
    source_review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=True)
    relevance_score = Column(Float, default=1.0)  # Decays over time
    access_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# v2.0 — Enterprise Guard
# ---------------------------------------------------------------------------


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(128), nullable=False)  # review.created, template.forked, etc.
    actor = Column(String(256), nullable=True)  # User or agent identifier
    resource_type = Column(String(64), nullable=False)  # review, template, org
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, default=dict)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SecurityPolicy(Base):
    __tablename__ = "security_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, unique=True)
    policy_type = Column(String(64), nullable=False)  # rate_limit, secret_detection, access_control
    config = Column(JSONB, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# v2.0 — Marketplace
# ---------------------------------------------------------------------------


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_type = Column(String(64), nullable=False)  # template, org, agent
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(128), nullable=True)
    version = Column(String(32), default="1.0.0")
    config = Column(JSONB, default=dict)  # The template/org/agent definition
    tags = Column(JSONB, default=list)  # ["security", "python", "fast"]
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# v3.0 — Self-hosting Agent Company
# ---------------------------------------------------------------------------


class AgentCompany(Base):
    __tablename__ = "agent_companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    owner = Column(String(256), nullable=True)
    org_chart = Column(JSONB, default=dict)  # Hierarchical agent structure
    processes = Column(JSONB, default=list)  # Defined workflows
    shared_state = Column(JSONB, default=dict)  # Company-wide shared memory
    budget_usd = Column(Numeric(10, 2), default=0)  # Budget limit
    spent_usd = Column(Numeric(10, 6), default=0)  # Current spend
    status = Column(String(20), default="draft")  # draft, active, paused, archived
    agent_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agents = relationship("CompanyAgent", back_populates="company", cascade="all, delete-orphan",
                          foreign_keys="CompanyAgent.company_id")
    proposals = relationship("Proposal", back_populates="company", cascade="all, delete-orphan")


class CompanyAgent(Base):
    __tablename__ = "company_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("agent_companies.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(128), nullable=False)
    title = Column(String(256), nullable=True)
    model = Column(String(128), default="claude-sonnet")
    system_prompt = Column(Text, nullable=True)
    capabilities = Column(JSONB, default=list)
    reports_to = Column(UUID(as_uuid=True), ForeignKey("company_agents.id"), nullable=True)
    status = Column(String(20), default="idle")
    total_tasks = Column(Integer, default=0)
    total_cost_usd = Column(Numeric(10, 6), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("AgentCompany", back_populates="agents", foreign_keys=[company_id])


# ---------------------------------------------------------------------------
# v3.0 — DAO Governance
# ---------------------------------------------------------------------------


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("agent_companies.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    proposal_type = Column(String(64), nullable=False)  # budget, role_change, process, policy
    proposed_changes = Column(JSONB, default=dict)
    proposed_by = Column(UUID(as_uuid=True), ForeignKey("company_agents.id"), nullable=True)
    status = Column(String(20), default="open")  # open, passed, rejected, executed
    votes_for = Column(Integer, default=0)
    votes_against = Column(Integer, default=0)
    quorum_required = Column(Integer, default=3)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("AgentCompany", back_populates="proposals")
    votes = relationship("Vote", back_populates="proposal", cascade="all, delete-orphan")


class Vote(Base):
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False)
    voter_id = Column(UUID(as_uuid=True), ForeignKey("company_agents.id"), nullable=False)
    vote = Column(String(10), nullable=False)  # for, against, abstain
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    proposal = relationship("Proposal", back_populates="votes")


# ---------------------------------------------------------------------------
# v3.0 — AI Science Engine
# ---------------------------------------------------------------------------


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("agent_companies.id"), nullable=True)
    title = Column(String(256), nullable=False)
    hypothesis = Column(Text, nullable=True)
    methodology = Column(JSONB, default=dict)
    status = Column(String(20), default="draft")  # draft, running, analyzing, completed, published
    variables = Column(JSONB, default=dict)  # Independent, dependent, controlled
    results = Column(JSONB, default=dict)
    analysis = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    total_runs = Column(Integer, default=0)
    total_cost_usd = Column(Numeric(10, 6), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    runs = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    run_number = Column(Integer, nullable=False)
    parameters = Column(JSONB, default=dict)
    results = Column(JSONB, default=dict)
    metrics = Column(JSONB, default=dict)
    status = Column(String(20), default="pending")
    duration_seconds = Column(Float, default=0.0)
    cost_usd = Column(Numeric(10, 6), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="runs")
