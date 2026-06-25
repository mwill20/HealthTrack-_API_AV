"""
app/health.py
Readiness probe for HealthTrack API.

Exposes GET /health, which reports whether the API can currently reach its
two backing services — PostgreSQL and Redis. Consumed by:
  - the Docker HEALTHCHECK instruction
  - docker-compose `depends_on: condition: service_healthy` gating
  - external load balancers / orchestrators

Security note: dependency failures are logged in full *server-side* only.
The HTTP response returns a coarse "ok"/"error" per dependency and never
echoes connection strings, hostnames, or driver exceptions to the caller —
that would leak internal topology to an unauthenticated client. (Contrast
app/alerts.py, which intentionally leaks internals: a teaching anti-pattern.)
"""

import logging
import os

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)

# Bound connection attempts so a dead dependency fails fast instead of hanging
# the probe (and, transitively, the container HEALTHCHECK and compose startup).
_CONNECT_TIMEOUT_SECONDS = 2


def _check_database() -> bool:
    """Return True if a trivial query against PostgreSQL succeeds."""
    import psycopg2

    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "healthtrack"),
            user=os.getenv("DB_USER", "healthtrack"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=_CONNECT_TIMEOUT_SECONDS,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception:
        logger.exception("Database health check failed")
        return False
    finally:
        if conn is not None:
            conn.close()


def _check_cache() -> bool:
    """Return True if Redis responds to PING."""
    import redis

    try:
        client = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            socket_connect_timeout=_CONNECT_TIMEOUT_SECONDS,
        )
        return bool(client.ping())
    except Exception:
        logger.exception("Cache health check failed")
        return False


@health_bp.route("/health", methods=["GET"])
def health():
    """Report API liveness plus backing-service status.

    Always returns HTTP 200 while the process is serving — this is a liveness
    signal, so it stays green even when run standalone without a database or
    cache (e.g. `docker run` of just the image). The JSON body reports each
    dependency's reachability ("ok"/"error") for observability.

    Startup ordering in docker-compose is enforced by the *database* and
    *cache* services' own healthchecks (pg_isready / redis-cli ping) that the
    api waits on via depends_on — not by this endpoint's status code.
    """
    db_ok = _check_database()
    cache_ok = _check_cache()

    body = {
        "status": "ok" if (db_ok and cache_ok) else "degraded",
        "database": "ok" if db_ok else "error",
        "cache": "ok" if cache_ok else "error",
    }
    return jsonify(body), 200
