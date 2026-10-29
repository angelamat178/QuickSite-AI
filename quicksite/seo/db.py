from __future__ import annotations
import os
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL

DEFAULT_DB = "sqlite:///./data/quicksite_seo.db"

def make_engine(url: str | URL | None = None) -> Engine:
    configured = url or os.getenv("QUICKSITE_DATABASE_URL")
    if not configured:
        # Resolve the default path from the project, not the current working directory.
        db_path = Path(__file__).resolve().parents[2] / "data" / "quicksite_seo.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        configured = URL.create("sqlite", database=str(db_path))
    driver = configured.drivername if isinstance(configured, URL) else configured.split(":", 1)[0]
    connect_args = {"check_same_thread": False} if driver.startswith("sqlite") else {}
    return create_engine(configured, future=True, pool_pre_ping=True, connect_args=connect_args)

SCHEMA = """
CREATE TABLE IF NOT EXISTS site_profiles (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, base_url TEXT NOT NULL,
 gsc_property TEXT, ga4_property_id TEXT, wp_api_url TEXT, sitemap_url TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS pages (
 id INTEGER PRIMARY KEY AUTOINCREMENT, site_profile_id INTEGER NOT NULL, url TEXT NOT NULL,
 normalized_url TEXT NOT NULL, title TEXT, wp_id INTEGER, wp_type TEXT, wp_status TEXT,
 canonical_url TEXT, meta_description TEXT, robots TEXT, http_status INTEGER,
 h1 TEXT, word_count INTEGER, source TEXT NOT NULL DEFAULT 'manual',
 last_crawled_at TEXT, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(site_profile_id, normalized_url),
 FOREIGN KEY(site_profile_id) REFERENCES site_profiles(id)
);
CREATE TABLE IF NOT EXISTS metric_snapshots (
 id INTEGER PRIMARY KEY AUTOINCREMENT, site_profile_id INTEGER NOT NULL, page_id INTEGER,
 source TEXT NOT NULL, metric_date TEXT NOT NULL, period_start TEXT, period_end TEXT,
 dimensions_json TEXT NOT NULL DEFAULT '{}', metrics_json TEXT NOT NULL,
 fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, coverage TEXT NOT NULL DEFAULT 'unknown',
 FOREIGN KEY(site_profile_id) REFERENCES site_profiles(id), FOREIGN KEY(page_id) REFERENCES pages(id)
);
CREATE INDEX IF NOT EXISTS ix_metrics_page_date ON metric_snapshots(page_id, metric_date, source);
CREATE TABLE IF NOT EXISTS conversions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, site_profile_id INTEGER NOT NULL, page_id INTEGER,
 event_date TEXT NOT NULL, source TEXT NOT NULL, event_name TEXT NOT NULL,
 count INTEGER NOT NULL DEFAULT 0, qualified_count INTEGER, customer_count INTEGER,
 attribution_json TEXT NOT NULL DEFAULT '{}', measurement_status TEXT NOT NULL DEFAULT 'measured',
 FOREIGN KEY(site_profile_id) REFERENCES site_profiles(id), FOREIGN KEY(page_id) REFERENCES pages(id)
);
CREATE TABLE IF NOT EXISTS link_edges (
 id INTEGER PRIMARY KEY AUTOINCREMENT, site_profile_id INTEGER NOT NULL, source_page_id INTEGER NOT NULL,
 target_page_id INTEGER, target_url TEXT NOT NULL, anchor_text TEXT, status_code INTEGER,
 discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(site_profile_id) REFERENCES site_profiles(id), FOREIGN KEY(source_page_id) REFERENCES pages(id)
);
CREATE TABLE IF NOT EXISTS rules (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
 severity TEXT NOT NULL DEFAULT 'medium', config_json TEXT NOT NULL DEFAULT '{}', version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS recommendations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, site_profile_id INTEGER NOT NULL, page_id INTEGER,
 rule_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', title TEXT NOT NULL,
 explanation TEXT NOT NULL, evidence_json TEXT NOT NULL, impact TEXT NOT NULL DEFAULT 'unknown',
 confidence TEXT NOT NULL DEFAULT 'medium', effort TEXT NOT NULL DEFAULT 'medium',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(site_profile_id) REFERENCES site_profiles(id), FOREIGN KEY(page_id) REFERENCES pages(id)
);
CREATE TABLE IF NOT EXISTS sync_runs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, site_profile_id INTEGER NOT NULL, source TEXT NOT NULL,
 status TEXT NOT NULL, started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, finished_at TEXT,
 rows_read INTEGER NOT NULL DEFAULT 0, message TEXT, metadata_json TEXT NOT NULL DEFAULT '{}',
 FOREIGN KEY(site_profile_id) REFERENCES site_profiles(id)
);
"""

def init_db(engine: Engine) -> None:
    with engine.begin() as conn:
        dialect = engine.dialect.name
        schema = SCHEMA
        if dialect == "postgresql":
            schema = schema.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        for statement in schema.strip().split(";"):
            if statement.strip():
                conn.execute(text(statement))

@contextmanager
def transaction(engine: Engine):
    with engine.begin() as conn:
        yield conn
