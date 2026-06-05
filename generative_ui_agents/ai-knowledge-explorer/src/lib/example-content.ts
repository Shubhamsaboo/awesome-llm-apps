export const EXAMPLE_FILES = [
  {
    name: "what-are-agents.md",
    content: `# What Are AI Agents?

An AI agent is a system that uses a large language model (LLM) as its core reasoning engine to decide what actions to take. Unlike simple chatbots that just generate text, agents can use tools, maintain memory across conversations, and plan multi-step workflows.

## Core Components

**LLM (Brain)**: The language model that reasons about the task and decides the next action. Models like GPT-4, Claude, and Gemini serve as the reasoning core.

**Tools**: External capabilities the agent can invoke — web search, code execution, database queries, API calls. Tools are what separate an agent from a chatbot.

**Memory**: Short-term (conversation context) and long-term (persistent knowledge). Without memory, agents can't learn from past interactions or maintain state across sessions.

**Planning**: The ability to break complex tasks into subtasks, execute them in order, and adjust the plan based on intermediate results. ReAct (Reason + Act) and Chain of Thought are common planning patterns.

## How Agents Work

1. User gives a goal
2. Agent reasons about what tools and steps are needed
3. Agent executes tools, observes results
4. Agent reasons again based on observations
5. Repeat until the goal is achieved or the agent decides it can't proceed

This observe-think-act loop is the fundamental pattern. The LLM handles the "think" part, tools handle the "act" part, and the framework orchestrates the loop.

## Agent vs. Chatbot

A chatbot generates text responses. An agent takes actions in the world. The key difference is agency — the ability to affect external systems, not just produce text. A chatbot tells you the weather. An agent checks the weather API, books an umbrella delivery, and sends you a calendar reminder.`,
  },
  {
    name: "agent-frameworks.md",
    content: `# Agent Frameworks Compared

Several frameworks have emerged for building AI agents. Each makes different trade-offs between flexibility, ease of use, and multi-agent support.

## LangGraph

Built by LangChain. Models agent workflows as state machines (directed graphs). Each node is a step, edges define transitions. Supports cycles (loops), conditional branching, and human-in-the-loop checkpoints. Best for complex, stateful workflows where you need fine-grained control. Used heavily in production systems.

## CrewAI

Focuses on multi-agent collaboration. You define "crews" of agents with specific roles (researcher, writer, reviewer). Agents collaborate via a shared task pipeline. Simpler than LangGraph for multi-agent scenarios but less flexible for single-agent workflows. Good for content generation and research pipelines.

## AutoGen (Microsoft)

Multi-agent conversation framework. Agents communicate via messages in a group chat pattern. Supports code execution, human feedback, and nested conversations. Strong in code generation and data analysis tasks. More research-oriented than production-ready.

## CopilotKit

Designed for building AI copilots embedded in applications. Focuses on shared state between the agent and the UI — the agent can manipulate application state, and users can interact with the same state. Uses a protocol called AG-UI for real-time state streaming. Best for interactive applications where the agent needs to render UI, not just text.

## Key Differences

LangGraph and CopilotKit are complementary — LangGraph handles the agent logic, CopilotKit handles the UI integration. CrewAI and AutoGen focus on multi-agent orchestration but don't address UI rendering. All frameworks use LLMs as the reasoning engine but differ in how they structure the agent loop and handle state.`,
  },
  {
    name: "agent-challenges.md",
    content: `# Challenges in AI Agent Development

Building reliable agents is harder than building chatbots. Several fundamental challenges remain unsolved or partially addressed.

## Hallucination

LLMs generate plausible but incorrect information. In agents, this is worse because hallucinated tool calls or parameters cause real-world failures. An agent that hallucinates a file path will try to read a nonexistent file. Grounding techniques (RAG, tool validation, structured output) reduce but don't eliminate this risk.

## Tool Reliability

Tools fail. APIs timeout. Databases go down. Rate limits hit. Agents need robust error handling and retry logic, but most frameworks treat tools as reliable black boxes. The gap between "tool works in demo" and "tool works in production" is significant.

## Evaluation

How do you know if an agent is good? Traditional metrics (accuracy, F1) don't capture agent quality. You need to evaluate: Did it choose the right tools? Did it plan efficiently? Did it recover from errors? Agent evaluation is an emerging field — LLM-as-judge, trajectory analysis, and task completion rates are common approaches.

## Cost and Latency

Agents make multiple LLM calls per task. A simple research task might require 5-10 LLM calls. At current pricing, complex agent workflows can cost \\$0.50-2.00 per task. Latency compounds too — each LLM call adds 1-5 seconds, so a 10-step agent takes 10-50 seconds.

## Context Window Limits

Even with 100K+ token context windows, agents that process many documents or have long conversations will hit limits. Strategies include summarization, RAG for selective retrieval, and hierarchical agents that delegate to sub-agents with their own context windows.

## Security

Agents with tool access can be manipulated through prompt injection. A malicious document could instruct the agent to exfiltrate data or delete files. Sandboxing tool access, validating tool inputs, and maintaining least-privilege principles are essential but rarely implemented in demo agents.`,
  },
];

export const CODE_EXAMPLE_FILES = [
  {
    name: "auth.py",
    content: `"""Authentication module for the API service."""
from datetime import datetime, timedelta
from typing import Optional

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import User
from app.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


class TokenService:
    def __init__(self, db: Session):
        self.db = db

    def create_token_pair(self, user: User) -> dict:
        access_token = create_access_token({"sub": str(user.id), "role": user.role})
        refresh_token = create_access_token(
            {"sub": str(user.id), "type": "refresh"},
            expires_delta=timedelta(days=7),
        )
        return {"access_token": access_token, "refresh_token": refresh_token}

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")


class TokenExpiredError(Exception):
    pass


class InvalidTokenError(Exception):
    pass`,
  },
  {
    name: "routes.py",
    content: `"""API route handlers for user authentication and management."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import authenticate_user, TokenService, TokenExpiredError, InvalidTokenError
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, TokenResponse


router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    token_service = TokenService(db)
    try:
        payload = token_service.verify_token(token)
    except (TokenExpiredError, InvalidTokenError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User.create(db, user_data)
    return user


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token_service = TokenService(db)
    tokens = token_service.create_token_pair(user)
    return tokens


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    token_service = TokenService(db)
    try:
        payload = token_service.verify_token(token)
    except (TokenExpiredError, InvalidTokenError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a refresh token")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return token_service.create_token_pair(user)`,
  },
  {
    name: "models.py",
    content: `"""SQLAlchemy models for the application."""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import Session, relationship

from app.auth import get_password_hash
from app.database import Base


class UserRole(str, PyEnum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    @classmethod
    def create(cls, db: Session, user_data) -> "User":
        user = cls(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, default=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="posts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    resource = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")`,
  },
];
