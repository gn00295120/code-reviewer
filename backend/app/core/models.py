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
