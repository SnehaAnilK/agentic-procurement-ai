"""
database.py — SQL database layer for the Market Research Engine.

Stores every research run so you can track:
  • Sentiment trends over time per topic
  • All articles ever scraped
  • Full analysis history

Schema:
  research_runs  — one row per pipeline run
  articles       — every article scraped (linked to a run)
  trends         — extracted trends (linked to a run)
  risks          — extracted risks (linked to a run)
  recommendations — extracted recommendations (linked to a run)

Works with SQLite (zero setup, file-based) by default.
Swap the DATABASE_URL in .env to connect to PostgreSQL for production.
"""

import os
import json
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, Float, String,
    Text, DateTime, ForeignKey, inspect
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from colorama import Fore, Style

import config

# ─── Engine Setup ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///output/research_history.db")

engine  = create_engine(DATABASE_URL, echo=False,
                        connect_args={"check_same_thread": False}
                        if "sqlite" in DATABASE_URL else {})
Session = sessionmaker(bind=engine)
Base    = declarative_base()


# ─── Models ───────────────────────────────────────────────────────────────────

class ResearchRun(Base):
    __tablename__ = "research_runs"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    topic            = Column(String(255), nullable=False, index=True)
    run_date         = Column(DateTime, default=datetime.utcnow, index=True)
    articles_used    = Column(Integer)
    sentiment_score  = Column(Float)
    confidence_score = Column(Float)
    sources          = Column(Text)       # JSON list
    date_range_from  = Column(String(20))
    date_range_to    = Column(String(20))
    pdf_path         = Column(String(512))
    executive_summary = Column(Text)

    # Relationships
    articles        = relationship("Article",       back_populates="run", cascade="all, delete")
    trends          = relationship("Trend",         back_populates="run", cascade="all, delete")
    risks           = relationship("Risk",          back_populates="run", cascade="all, delete")
    bottlenecks     = relationship("Bottleneck",    back_populates="run", cascade="all, delete")
    recommendations = relationship("Recommendation",back_populates="run", cascade="all, delete")


class Article(Base):
    __tablename__ = "articles"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    run_id    = Column(Integer, ForeignKey("research_runs.id"), nullable=False)
    title     = Column(String(512))
    source    = Column(String(255))
    url       = Column(Text)
    published = Column(String(20))
    summary   = Column(Text)

    run = relationship("ResearchRun", back_populates="articles")


class Trend(Base):
    __tablename__ = "trends"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    run_id   = Column(Integer, ForeignKey("research_runs.id"), nullable=False)
    trend    = Column(Text)
    evidence = Column(Text)
    impact   = Column(String(20))

    run = relationship("ResearchRun", back_populates="trends")


class Risk(Base):
    __tablename__ = "risks"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    run_id     = Column(Integer, ForeignKey("research_runs.id"), nullable=False)
    risk       = Column(Text)
    severity   = Column(String(20))
    mitigation = Column(Text)

    run = relationship("ResearchRun", back_populates="risks")


class Bottleneck(Base):
    __tablename__ = "bottlenecks"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    run_id         = Column(Integer, ForeignKey("research_runs.id"), nullable=False)
    bottleneck     = Column(Text)
    affected_area  = Column(Text)
    recommendation = Column(Text)

    run = relationship("ResearchRun", back_populates="bottlenecks")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    run_id     = Column(Integer, ForeignKey("research_runs.id"), nullable=False)
    priority   = Column(Integer)
    action     = Column(Text)
    rationale  = Column(Text)
    timeline   = Column(String(30))

    run = relationship("ResearchRun", back_populates="recommendations")


# ─── Init ─────────────────────────────────────────────────────────────────────

def init_db():
    """Create all tables if they don't exist yet."""
    os.makedirs("output", exist_ok=True)
    Base.metadata.create_all(engine)
    print(f"  {Fore.GREEN}✔  Database ready:{Style.RESET_ALL} {DATABASE_URL}")


# ─── Save Run ─────────────────────────────────────────────────────────────────

def save_run(df, analysis: dict, pdf_path: str = "") -> int:
    """
    Persist a completed research run to the database.
    Returns the new run ID.
    """
    session = Session()
    try:
        run = ResearchRun(
            topic             = analysis.get("topic", ""),
            run_date          = datetime.utcnow(),
            articles_used     = analysis.get("articles_used", 0),
            sentiment_score   = analysis.get("sentiment_score", 0),
            confidence_score  = analysis.get("confidence_score", 0),
            sources           = json.dumps(analysis.get("sources", [])),
            date_range_from   = analysis.get("date_range", {}).get("from", ""),
            date_range_to     = analysis.get("date_range", {}).get("to", ""),
            pdf_path          = pdf_path,
            executive_summary = analysis.get("executive_summary", ""),
        )
        session.add(run)
        session.flush()   # get run.id before commit

        # Articles
        for _, row in df.iterrows():
            session.add(Article(
                run_id    = run.id,
                title     = row.get("title", ""),
                source    = row.get("source", ""),
                url       = row.get("url", ""),
                published = row.get("published", ""),
                summary   = row.get("summary", ""),
            ))

        # Trends
        for t in analysis.get("key_trends", []):
            session.add(Trend(
                run_id   = run.id,
                trend    = t.get("trend", ""),
                evidence = t.get("evidence", ""),
                impact   = t.get("impact", ""),
            ))

        # Risks
        for r in analysis.get("risk_factors", []):
            session.add(Risk(
                run_id     = run.id,
                risk       = r.get("risk", ""),
                severity   = r.get("severity", ""),
                mitigation = r.get("mitigation", ""),
            ))

        # Bottlenecks
        for b in analysis.get("operational_bottlenecks", []):
            session.add(Bottleneck(
                run_id         = run.id,
                bottleneck     = b.get("bottleneck", ""),
                affected_area  = b.get("affected_area", ""),
                recommendation = b.get("recommendation", ""),
            ))

        # Recommendations
        for rec in analysis.get("strategic_recommendations", []):
            session.add(Recommendation(
                run_id    = run.id,
                priority  = rec.get("priority", 0),
                action    = rec.get("action", ""),
                rationale = rec.get("rationale", ""),
                timeline  = rec.get("timeline", ""),
            ))

        session.commit()
        run_id = run.id
        print(f"  {Fore.GREEN}✔  Saved to database:{Style.RESET_ALL} Run ID {run_id}")
        return run_id

    except Exception as e:
        session.rollback()
        print(f"  {Fore.RED}✘  DB save failed: {e}{Style.RESET_ALL}")
        raise
    finally:
        session.close()


# ─── Query Helpers (used by Streamlit dashboard) ──────────────────────────────

def get_all_runs() -> list[dict]:
    """Return all runs as a list of dicts (for dashboard history table)."""
    session = Session()
    try:
        runs = session.query(ResearchRun).order_by(ResearchRun.run_date.desc()).all()
        return [
            {
                "id":               r.id,
                "topic":            r.topic,
                "run_date":         r.run_date.strftime("%Y-%m-%d %H:%M"),
                "articles_used":    r.articles_used,
                "sentiment_score":  round(r.sentiment_score or 0, 3),
                "confidence_score": round(r.confidence_score or 0, 3),
                "pdf_path":         r.pdf_path,
            }
            for r in runs
        ]
    finally:
        session.close()


def get_sentiment_history(topic: str) -> list[dict]:
    """
    Return sentiment scores over time for a specific topic.
    Used for Power BI / Streamlit line chart.
    """
    session = Session()
    try:
        runs = (
            session.query(ResearchRun)
            .filter(ResearchRun.topic.ilike(f"%{topic}%"))
            .order_by(ResearchRun.run_date.asc())
            .all()
        )
        return [
            {
                "date":             r.run_date.strftime("%Y-%m-%d"),
                "sentiment_score":  round(r.sentiment_score or 0, 3),
                "confidence_score": round(r.confidence_score or 0, 3),
                "articles_used":    r.articles_used,
            }
            for r in runs
        ]
    finally:
        session.close()


def get_run_details(run_id: int) -> dict:
    """Return full details of a single run including all linked records."""
    session = Session()
    try:
        r = session.query(ResearchRun).filter_by(id=run_id).first()
        if not r:
            return {}
        return {
            "id":               r.id,
            "topic":            r.topic,
            "run_date":         r.run_date.strftime("%Y-%m-%d %H:%M"),
            "executive_summary": r.executive_summary,
            "sentiment_score":  r.sentiment_score,
            "confidence_score": r.confidence_score,
            "articles_used":    r.articles_used,
            "pdf_path":         r.pdf_path,
            "trends":      [{"trend": t.trend, "impact": t.impact} for t in r.trends],
            "risks":       [{"risk": t.risk, "severity": t.severity} for t in r.risks],
            "recommendations": [{"action": t.action, "timeline": t.timeline} for t in r.recommendations],
        }
    finally:
        session.close()
