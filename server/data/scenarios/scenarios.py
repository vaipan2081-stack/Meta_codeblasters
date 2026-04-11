"""
Predefined incident scenarios for each difficulty tier.

Each scenario contains:
- A simulated distributed system topology
- Injected faults with ground truth
- Realistic log streams, metrics, alerts, and traces
"""

from __future__ import annotations

import copy
import random
from datetime import datetime, timedelta
from typing import Any

# ── Service Definitions ─────────────────────────────────────────────────────

SERVICES_CATALOG = {
    "api-gateway": {
        "type": "api-gateway",
        "version": "2.4.1",
        "dependencies": ["auth-service", "order-service", "user-service"],
    },
    "auth-service": {
        "type": "authentication",
        "version": "1.8.3",
        "dependencies": ["user-db", "redis-cache"],
    },
    "order-service": {
        "type": "business-logic",
        "version": "3.2.0",
        "dependencies": ["order-db", "payment-service", "inventory-service", "kafka-broker"],
    },
    "payment-service": {
        "type": "payment-processor",
        "version": "2.1.5",
        "dependencies": ["payment-db", "stripe-connector"],
    },
    "inventory-service": {
        "type": "business-logic",
        "version": "1.5.2",
        "dependencies": ["inventory-db", "kafka-broker"],
    },
    "user-service": {
        "type": "business-logic",
        "version": "2.0.1",
        "dependencies": ["user-db", "redis-cache"],
    },
    "notification-service": {
        "type": "messaging",
        "version": "1.3.0",
        "dependencies": ["kafka-broker", "smtp-relay"],
    },
    "order-db": {
        "type": "database",
        "version": "14.2-pg",
        "dependencies": [],
    },
    "user-db": {
        "type": "database",
        "version": "14.2-pg",
        "dependencies": [],
    },
    "payment-db": {
        "type": "database",
        "version": "8.0-mysql",
        "dependencies": [],
    },
    "inventory-db": {
        "type": "database",
        "version": "6.2-mongo",
        "dependencies": [],
    },
    "redis-cache": {
        "type": "cache",
        "version": "7.2.0",
        "dependencies": [],
    },
    "kafka-broker": {
        "type": "message-queue",
        "version": "3.6.0",
        "dependencies": [],
    },
    "stripe-connector": {
        "type": "external-integration",
        "version": "1.0.4",
        "dependencies": [],
    },
    "smtp-relay": {
        "type": "external-integration",
        "version": "1.1.0",
        "dependencies": [],
    },
}


def _ts(base: datetime, offset_seconds: int) -> str:
    return (base + timedelta(seconds=offset_seconds)).isoformat() + "Z"


# ── Easy Scenarios ──────────────────────────────────────────────────────────

def _easy_scenario_1(seed: int) -> dict[str, Any]:
    """OOM crash in order-db causing 500s on order-service."""
    rng = random.Random(seed)
    base = datetime(2025, 3, 15, 14, 30, 0)
    services_used = [
        "api-gateway", "order-service", "order-db",
        "auth-service", "user-service", "redis-cache",
    ]

    logs = [
        # Normal traffic
        {"timestamp": _ts(base, 0), "service": "api-gateway", "level": "INFO",
         "message": "POST /api/v1/orders -> order-service (200)", "trace_id": "tr-001"},
        {"timestamp": _ts(base, 5), "service": "order-service", "level": "INFO",
         "message": "Processing order #ORD-29481 for user U-1052", "trace_id": "tr-001"},
        {"timestamp": _ts(base, 6), "service": "order-db", "level": "INFO",
         "message": "INSERT INTO orders VALUES (...) completed in 12ms", "trace_id": "tr-001"},
        # DB starts struggling
        {"timestamp": _ts(base, 30), "service": "order-db", "level": "WARNING",
         "message": "Memory usage at 87% (6.96GB / 8GB), approaching configured limit"},
        {"timestamp": _ts(base, 45), "service": "order-db", "level": "WARNING",
         "message": "Slow query detected: SELECT * FROM orders WHERE status='pending' took 4200ms"},
        {"timestamp": _ts(base, 60), "service": "order-db", "level": "ERROR",
         "message": "FATAL: out of memory. PostgreSQL process killed by OOM killer (pid=2847)"},
        {"timestamp": _ts(base, 61), "service": "order-db", "level": "CRITICAL",
         "message": "Database connection pool exhausted. All 50 connections in CLOSED state."},
        # Cascading to order-service
        {"timestamp": _ts(base, 62), "service": "order-service", "level": "ERROR",
         "message": "ConnectionRefusedError: Cannot connect to order-db at 10.0.3.15:5432", "trace_id": "tr-002"},
        {"timestamp": _ts(base, 63), "service": "order-service", "level": "ERROR",
         "message": "Failed to process order #ORD-29482: database unavailable", "trace_id": "tr-002"},
        {"timestamp": _ts(base, 64), "service": "api-gateway", "level": "ERROR",
         "message": "POST /api/v1/orders -> order-service (503 Service Unavailable)", "trace_id": "tr-002"},
        # More failures
        {"timestamp": _ts(base, 70), "service": "order-service", "level": "ERROR",
         "message": "Circuit breaker OPEN for order-db connections after 5 consecutive failures"},
        {"timestamp": _ts(base, 75), "service": "api-gateway", "level": "ERROR",
         "message": "POST /api/v1/orders -> order-service (503 Service Unavailable)", "trace_id": "tr-003"},
        {"timestamp": _ts(base, 80), "service": "api-gateway", "level": "WARNING",
         "message": "Error rate for /api/v1/orders exceeded 50% threshold in last 60s"},
        # Normal services still fine
        {"timestamp": _ts(base, 65), "service": "auth-service", "level": "INFO",
         "message": "Token validation for user U-1053 successful"},
        {"timestamp": _ts(base, 68), "service": "user-service", "level": "INFO",
         "message": "GET /api/v1/users/U-1053 completed in 8ms"},
        {"timestamp": _ts(base, 72), "service": "redis-cache", "level": "INFO",
         "message": "Cache HIT for key session:U-1053, memory usage 45%"},
    ]

    metrics = {
        "order-db": {
            "memory_usage_percent": [
                {"timestamp": _ts(base, -300), "value": 62.0},
                {"timestamp": _ts(base, -240), "value": 65.0},
                {"timestamp": _ts(base, -180), "value": 71.0},
                {"timestamp": _ts(base, -120), "value": 78.0},
                {"timestamp": _ts(base, -60), "value": 85.0},
                {"timestamp": _ts(base, 0), "value": 87.0},
                {"timestamp": _ts(base, 30), "value": 93.0},
                {"timestamp": _ts(base, 60), "value": 99.8},
            ],
            "query_latency_ms": [
                {"timestamp": _ts(base, -300), "value": 15.0},
                {"timestamp": _ts(base, -120), "value": 45.0},
                {"timestamp": _ts(base, 0), "value": 220.0},
                {"timestamp": _ts(base, 30), "value": 1800.0},
                {"timestamp": _ts(base, 45), "value": 4200.0},
            ],
            "connections_active": [
                {"timestamp": _ts(base, -300), "value": 22.0},
                {"timestamp": _ts(base, 0), "value": 35.0},
                {"timestamp": _ts(base, 30), "value": 48.0},
                {"timestamp": _ts(base, 60), "value": 0.0},
            ],
        },
        "order-service": {
            "error_rate_percent": [
                {"timestamp": _ts(base, -300), "value": 0.1},
                {"timestamp": _ts(base, 0), "value": 0.2},
                {"timestamp": _ts(base, 60), "value": 78.0},
                {"timestamp": _ts(base, 80), "value": 95.0},
            ],
            "request_latency_p99_ms": [
                {"timestamp": _ts(base, -300), "value": 120.0},
                {"timestamp": _ts(base, 0), "value": 180.0},
                {"timestamp": _ts(base, 30), "value": 5500.0},
                {"timestamp": _ts(base, 60), "value": 30000.0},
            ],
        },
        "api-gateway": {
            "http_5xx_rate": [
                {"timestamp": _ts(base, -300), "value": 0.01},
                {"timestamp": _ts(base, 60), "value": 0.52},
                {"timestamp": _ts(base, 80), "value": 0.68},
            ],
        },
    }

    alerts = [
        {"timestamp": _ts(base, 30), "service": "order-db", "severity": "warning",
         "title": "High Memory Usage",
         "description": "Memory usage on order-db exceeded 85% threshold."},
        {"timestamp": _ts(base, 60), "service": "order-db", "severity": "critical",
         "title": "Database Process Killed",
         "description": "PostgreSQL process terminated by OOM killer on order-db."},
        {"timestamp": _ts(base, 65), "service": "order-service", "severity": "critical",
         "title": "Upstream Dependency Failure",
         "description": "order-service cannot reach order-db. Circuit breaker activated."},
        {"timestamp": _ts(base, 80), "service": "api-gateway", "severity": "high",
         "title": "High Error Rate",
         "description": "5xx error rate for /api/v1/orders exceeds 50%."},
    ]

    traces = [
        {"trace_id": "tr-001", "span_id": "s-001", "parent_span_id": None,
         "service": "api-gateway", "operation": "POST /api/v1/orders",
         "duration_ms": 45.0, "status": "OK", "timestamp": _ts(base, 0)},
        {"trace_id": "tr-001", "span_id": "s-002", "parent_span_id": "s-001",
         "service": "order-service", "operation": "createOrder",
         "duration_ms": 38.0, "status": "OK", "timestamp": _ts(base, 1)},
        {"trace_id": "tr-001", "span_id": "s-003", "parent_span_id": "s-002",
         "service": "order-db", "operation": "INSERT orders",
         "duration_ms": 12.0, "status": "OK", "timestamp": _ts(base, 2)},
        {"trace_id": "tr-002", "span_id": "s-004", "parent_span_id": None,
         "service": "api-gateway", "operation": "POST /api/v1/orders",
         "duration_ms": 30002.0, "status": "ERROR", "timestamp": _ts(base, 62)},
        {"trace_id": "tr-002", "span_id": "s-005", "parent_span_id": "s-004",
         "service": "order-service", "operation": "createOrder",
         "duration_ms": 30000.0, "status": "ERROR", "timestamp": _ts(base, 62)},
    ]

    return {
        "scenario_id": "easy_oom_order_db",
        "difficulty": "easy",
        "services": services_used,
        "logs": logs,
        "metrics": metrics,
        "alerts": alerts,
        "traces": traces,
        "initial_alert": "CRITICAL: order-db process terminated by OOM killer. Multiple 503 errors on /api/v1/orders.",
        "ground_truth": {
            "root_cause": "Out-of-memory (OOM) crash on order-db PostgreSQL process due to memory limit exhaustion",
            "root_cause_service": "order-db",
            "affected_services": ["order-db", "order-service", "api-gateway"],
            "severity": "critical",
            "remediation": "1. Restart order-db PostgreSQL process. 2. Increase memory limit from 8GB to 16GB. 3. Investigate and optimize slow queries causing excessive memory usage. 4. Add memory-based autoscaling alerts.",
            "key_evidence": [
                "order-db memory usage climbed from 62% to 99.8% over 5 minutes",
                "OOM killer terminated PostgreSQL pid 2847",
                "Connection pool fully exhausted (0 active connections after crash)",
                "order-service circuit breaker opened after 5 consecutive failures",
            ],
        },
    }


def _easy_scenario_2(seed: int) -> dict[str, Any]:
    """Redis cache failure causing auth-service timeouts."""
    base = datetime(2025, 3, 16, 9, 15, 0)
    services_used = [
        "api-gateway", "auth-service", "redis-cache",
        "user-service", "user-db",
    ]

    logs = [
        {"timestamp": _ts(base, 0), "service": "redis-cache", "level": "WARNING",
         "message": "Maxmemory limit reached. Eviction policy: allkeys-lru"},
        {"timestamp": _ts(base, 5), "service": "redis-cache", "level": "ERROR",
         "message": "MISCONF Redis is configured to save RDB snapshots, but is not able to persist to disk. Background save error."},
        {"timestamp": _ts(base, 10), "service": "redis-cache", "level": "CRITICAL",
         "message": "Segmentation fault at address 0x7f3a2c001000. Redis process aborting."},
        {"timestamp": _ts(base, 11), "service": "auth-service", "level": "ERROR",
         "message": "ConnectionError: Redis connection to 10.0.5.20:6379 refused"},
        {"timestamp": _ts(base, 12), "service": "auth-service", "level": "ERROR",
         "message": "Session lookup failed for token eyJhb...xN2Q - falling back to DB"},
        {"timestamp": _ts(base, 15), "service": "auth-service", "level": "WARNING",
         "message": "Session fallback to user-db adding 350ms latency per request"},
        {"timestamp": _ts(base, 20), "service": "user-db", "level": "WARNING",
         "message": "Connection pool utilization at 78% - unusual surge in session lookups"},
        {"timestamp": _ts(base, 30), "service": "api-gateway", "level": "WARNING",
         "message": "Auth middleware response time degraded: p99=2100ms (baseline=45ms)"},
        {"timestamp": _ts(base, 40), "service": "auth-service", "level": "ERROR",
         "message": "Token validation timeout after 5000ms for user U-3891"},
        {"timestamp": _ts(base, 42), "service": "api-gateway", "level": "ERROR",
         "message": "GET /api/v1/users/U-3891 -> 504 Gateway Timeout"},
        # Unrelated normal logs
        {"timestamp": _ts(base, 25), "service": "user-service", "level": "INFO",
         "message": "Profile update for user U-2200 completed successfully"},
    ]

    metrics = {
        "redis-cache": {
            "memory_usage_percent": [
                {"timestamp": _ts(base, -120), "value": 92.0},
                {"timestamp": _ts(base, -60), "value": 96.0},
                {"timestamp": _ts(base, 0), "value": 100.0},
                {"timestamp": _ts(base, 10), "value": 0.0},
            ],
            "connected_clients": [
                {"timestamp": _ts(base, -60), "value": 45.0},
                {"timestamp": _ts(base, 10), "value": 0.0},
            ],
        },
        "auth-service": {
            "request_latency_p99_ms": [
                {"timestamp": _ts(base, -120), "value": 45.0},
                {"timestamp": _ts(base, 15), "value": 2100.0},
                {"timestamp": _ts(base, 40), "value": 5000.0},
            ],
            "error_rate_percent": [
                {"timestamp": _ts(base, -120), "value": 0.05},
                {"timestamp": _ts(base, 30), "value": 35.0},
            ],
        },
    }

    alerts = [
        {"timestamp": _ts(base, 5), "service": "redis-cache", "severity": "warning",
         "title": "Redis Persistence Error",
         "description": "Redis cannot persist RDB snapshots to disk."},
        {"timestamp": _ts(base, 10), "service": "redis-cache", "severity": "critical",
         "title": "Redis Process Crash",
         "description": "Redis process terminated with segmentation fault."},
        {"timestamp": _ts(base, 30), "service": "auth-service", "severity": "high",
         "title": "Authentication Latency Spike",
         "description": "Auth service p99 latency exceeded 2000ms."},
    ]

    traces = []

    return {
        "scenario_id": "easy_redis_crash",
        "difficulty": "easy",
        "services": services_used,
        "logs": logs,
        "metrics": metrics,
        "alerts": alerts,
        "traces": traces,
        "initial_alert": "CRITICAL: Redis cache process crash. Authentication latency significantly degraded.",
        "ground_truth": {
            "root_cause": "Redis cache segmentation fault after maxmemory exhaustion and RDB persistence failure",
            "root_cause_service": "redis-cache",
            "affected_services": ["redis-cache", "auth-service", "api-gateway"],
            "severity": "critical",
            "remediation": "1. Restart Redis with increased maxmemory setting. 2. Fix disk permissions for RDB persistence. 3. Configure auth-service with circuit breaker for Redis fallback. 4. Add Redis memory monitoring alerts.",
            "key_evidence": [
                "Redis memory at 100% with eviction policy active",
                "RDB snapshot persistence failure",
                "Segfault crash in Redis process",
                "Auth service fell back to DB lookups with 350ms+ added latency",
            ],
        },
    }


# ── Medium Scenarios ────────────────────────────────────────────────────────

def _medium_scenario_1(seed: int) -> dict[str, Any]:
    """Kafka broker partition leader election storm causes event processing failures
    across order-service, inventory-service, and notification-service."""
    base = datetime(2025, 3, 17, 22, 45, 0)
    services_used = [
        "api-gateway", "order-service", "inventory-service",
        "notification-service", "kafka-broker", "order-db",
        "inventory-db",
    ]

    logs = [
        # Kafka starts having issues
        {"timestamp": _ts(base, 0), "service": "kafka-broker", "level": "WARNING",
         "message": "Broker 2 (10.0.8.12) failed to send heartbeat to controller. Last seen 15s ago."},
        {"timestamp": _ts(base, 5), "service": "kafka-broker", "level": "WARNING",
         "message": "ISR shrink for partition orders-events-3: replicas [1,2,3] -> ISR [1,3]"},
        {"timestamp": _ts(base, 10), "service": "kafka-broker", "level": "ERROR",
         "message": "Broker 2 removed from cluster. Triggering partition reassignment for 24 partitions."},
        {"timestamp": _ts(base, 12), "service": "kafka-broker", "level": "WARNING",
         "message": "Leader election in progress for partitions: orders-events-[2,3,7], inventory-updates-[1,4,5]"},
        {"timestamp": _ts(base, 15), "service": "kafka-broker", "level": "ERROR",
         "message": "UnderReplicatedPartitions count: 24. Min ISR not met for 8 partitions."},
        # Consumers start failing
        {"timestamp": _ts(base, 18), "service": "order-service", "level": "ERROR",
         "message": "KafkaConsumer: No leader available for partition orders-events-3. Retrying in 5s."},
        {"timestamp": _ts(base, 20), "service": "order-service", "level": "ERROR",
         "message": "Failed to publish OrderCreated event to orders-events topic: NotLeaderOrFollowerException"},
        {"timestamp": _ts(base, 22), "service": "inventory-service", "level": "ERROR",
         "message": "Consumer group 'inventory-consumers' rebalancing triggered. 12 partitions unassigned."},
        {"timestamp": _ts(base, 25), "service": "inventory-service", "level": "WARNING",
         "message": "Inventory update backlog growing: 847 pending events in local queue"},
        {"timestamp": _ts(base, 28), "service": "notification-service", "level": "ERROR",
         "message": "Failed to consume from notification-events: OffsetOutOfRangeError on partition 2"},
        {"timestamp": _ts(base, 30), "service": "notification-service", "level": "WARNING",
         "message": "Order confirmation emails delayed. Queue depth: 234 messages."},
        # order-service impact
        {"timestamp": _ts(base, 25), "service": "order-service", "level": "WARNING",
         "message": "Order #ORD-30112 created in DB but event publication failed. Inconsistency risk."},
        {"timestamp": _ts(base, 35), "service": "order-service", "level": "ERROR",
         "message": "Saga orchestrator timeout: inventory reservation for ORD-30112 not confirmed after 30s"},
        {"timestamp": _ts(base, 40), "service": "api-gateway", "level": "WARNING",
         "message": "POST /api/v1/orders response time degraded: p95=8500ms (baseline=200ms)"},
        # DB is fine - red herring
        {"timestamp": _ts(base, 15), "service": "order-db", "level": "INFO",
         "message": "Checkpoint complete: wrote 12847 buffers (2.4%); 0 transaction log file(s) added"},
        {"timestamp": _ts(base, 35), "service": "inventory-db", "level": "INFO",
         "message": "Connection pool: 18/100 active. Query performance nominal."},
    ]

    metrics = {
        "kafka-broker": {
            "under_replicated_partitions": [
                {"timestamp": _ts(base, -120), "value": 0.0},
                {"timestamp": _ts(base, 0), "value": 2.0},
                {"timestamp": _ts(base, 10), "value": 24.0},
                {"timestamp": _ts(base, 30), "value": 18.0},
            ],
            "leader_election_rate": [
                {"timestamp": _ts(base, -120), "value": 0.0},
                {"timestamp": _ts(base, 10), "value": 8.0},
                {"timestamp": _ts(base, 15), "value": 12.0},
            ],
            "active_brokers": [
                {"timestamp": _ts(base, -120), "value": 3.0},
                {"timestamp": _ts(base, 10), "value": 2.0},
            ],
            "consumer_lag_total": [
                {"timestamp": _ts(base, -120), "value": 12.0},
                {"timestamp": _ts(base, 20), "value": 450.0},
                {"timestamp": _ts(base, 40), "value": 1847.0},
            ],
        },
        "order-service": {
            "event_publish_failures": [
                {"timestamp": _ts(base, -120), "value": 0.0},
                {"timestamp": _ts(base, 20), "value": 15.0},
                {"timestamp": _ts(base, 40), "value": 42.0},
            ],
            "saga_timeout_count": [
                {"timestamp": _ts(base, -120), "value": 0.0},
                {"timestamp": _ts(base, 35), "value": 8.0},
            ],
        },
        "inventory-service": {
            "pending_event_backlog": [
                {"timestamp": _ts(base, -120), "value": 3.0},
                {"timestamp": _ts(base, 25), "value": 847.0},
                {"timestamp": _ts(base, 40), "value": 1234.0},
            ],
        },
    }

    alerts = [
        {"timestamp": _ts(base, 10), "service": "kafka-broker", "severity": "critical",
         "title": "Broker Node Failure",
         "description": "Kafka broker 2 removed from cluster. Partition reassignment in progress."},
        {"timestamp": _ts(base, 15), "service": "kafka-broker", "severity": "high",
         "title": "Under-Replicated Partitions",
         "description": "24 under-replicated partitions detected. Min ISR not met for 8."},
        {"timestamp": _ts(base, 22), "service": "inventory-service", "severity": "high",
         "title": "Consumer Group Rebalancing",
         "description": "Inventory consumer group rebalancing with 12 unassigned partitions."},
        {"timestamp": _ts(base, 35), "service": "order-service", "severity": "high",
         "title": "Saga Timeouts",
         "description": "Multiple order saga orchestrations timing out waiting for inventory confirmations."},
    ]

    traces = [
        {"trace_id": "tr-010", "span_id": "s-010", "parent_span_id": None,
         "service": "api-gateway", "operation": "POST /api/v1/orders",
         "duration_ms": 8500.0, "status": "ERROR", "timestamp": _ts(base, 38)},
        {"trace_id": "tr-010", "span_id": "s-011", "parent_span_id": "s-010",
         "service": "order-service", "operation": "createOrder",
         "duration_ms": 8450.0, "status": "ERROR", "timestamp": _ts(base, 38)},
        {"trace_id": "tr-010", "span_id": "s-012", "parent_span_id": "s-011",
         "service": "order-db", "operation": "INSERT orders",
         "duration_ms": 15.0, "status": "OK", "timestamp": _ts(base, 38)},
        {"trace_id": "tr-010", "span_id": "s-013", "parent_span_id": "s-011",
         "service": "kafka-broker", "operation": "PRODUCE orders-events",
         "duration_ms": 8400.0, "status": "ERROR", "timestamp": _ts(base, 38)},
    ]

    return {
        "scenario_id": "medium_kafka_broker_failure",
        "difficulty": "medium",
        "services": services_used,
        "logs": logs,
        "metrics": metrics,
        "alerts": alerts,
        "traces": traces,
        "initial_alert": "HIGH: Multiple saga timeouts in order-service. Consumer groups rebalancing. Event processing failures detected.",
        "ground_truth": {
            "root_cause": "Kafka broker 2 node failure causing partition leader election storm, disrupting event-driven communication across microservices",
            "root_cause_service": "kafka-broker",
            "affected_services": ["kafka-broker", "order-service", "inventory-service", "notification-service"],
            "severity": "critical",
            "remediation": "1. Investigate and restart failed broker 2 node. 2. Monitor partition reassignment completion. 3. Once broker recovers, verify ISR is restored for all partitions. 4. Replay failed events from order-service dead letter queue. 5. Add broker health monitoring and automatic failover.",
            "key_evidence": [
                "Broker 2 heartbeat failure and removal from cluster",
                "24 under-replicated partitions with leader elections",
                "NotLeaderOrFollowerException on event publishing",
                "Consumer group rebalancing across services",
                "DBs are healthy - ruling out database issues",
            ],
        },
    }


def _medium_scenario_2(seed: int) -> dict[str, Any]:
    """Payment service connection pool leak to payment-db causing order processing failures."""
    base = datetime(2025, 3, 18, 11, 0, 0)
    services_used = [
        "api-gateway", "order-service", "payment-service",
        "payment-db", "stripe-connector", "kafka-broker",
    ]

    logs = [
        {"timestamp": _ts(base, 0), "service": "payment-service", "level": "INFO",
         "message": "Processing payment for order ORD-31200. Amount: $149.99"},
        {"timestamp": _ts(base, 2), "service": "stripe-connector", "level": "INFO",
         "message": "Stripe API charge ch_3N8xyz created successfully"},
        {"timestamp": _ts(base, 60), "service": "payment-service", "level": "DEBUG",
         "message": "DB connection pool stats: active=42, idle=8, max=50"},
        {"timestamp": _ts(base, 120), "service": "payment-service", "level": "WARNING",
         "message": "DB connection pool stats: active=47, idle=3, max=50. High utilization warning."},
        {"timestamp": _ts(base, 150), "service": "payment-service", "level": "DEBUG",
         "message": "Potential connection leak detected: connection id=conn-387 held for 180s without query"},
        {"timestamp": _ts(base, 180), "service": "payment-service", "level": "ERROR",
         "message": "DB connection pool exhausted (50/50). Waiting for available connection... timeout=30s"},
        {"timestamp": _ts(base, 210), "service": "payment-service", "level": "ERROR",
         "message": "ConnectionPoolTimeoutError: Could not acquire connection within 30s for payment ORD-31245"},
        {"timestamp": _ts(base, 212), "service": "order-service", "level": "ERROR",
         "message": "Payment processing failed for ORD-31245: upstream timeout from payment-service"},
        {"timestamp": _ts(base, 215), "service": "api-gateway", "level": "ERROR",
         "message": "POST /api/v1/orders -> 500 (order-service reported payment failure)"},
        {"timestamp": _ts(base, 220), "service": "payment-service", "level": "ERROR",
         "message": "18 connections leaked: acquired but never released. Suspected code path: refund_processor.handle_partial_refund()"},
        # Red herring: stripe has a minor blip
        {"timestamp": _ts(base, 100), "service": "stripe-connector", "level": "WARNING",
         "message": "Stripe API response latency elevated: 1200ms (p99 baseline: 400ms)"},
        {"timestamp": _ts(base, 130), "service": "stripe-connector", "level": "INFO",
         "message": "Stripe API latency recovered to normal: 350ms"},
        # Kafka is fine
        {"timestamp": _ts(base, 200), "service": "kafka-broker", "level": "INFO",
         "message": "Topic payment-events: throughput normal at 45 msg/s"},
    ]

    metrics = {
        "payment-service": {
            "db_pool_active_connections": [
                {"timestamp": _ts(base, -300), "value": 15.0},
                {"timestamp": _ts(base, 0), "value": 28.0},
                {"timestamp": _ts(base, 60), "value": 42.0},
                {"timestamp": _ts(base, 120), "value": 47.0},
                {"timestamp": _ts(base, 180), "value": 50.0},
            ],
            "db_pool_wait_time_ms": [
                {"timestamp": _ts(base, -300), "value": 0.0},
                {"timestamp": _ts(base, 120), "value": 500.0},
                {"timestamp": _ts(base, 180), "value": 30000.0},
            ],
            "error_rate_percent": [
                {"timestamp": _ts(base, -300), "value": 0.1},
                {"timestamp": _ts(base, 180), "value": 45.0},
                {"timestamp": _ts(base, 220), "value": 68.0},
            ],
        },
        "payment-db": {
            "connections_total": [
                {"timestamp": _ts(base, -300), "value": 20.0},
                {"timestamp": _ts(base, 120), "value": 50.0},
                {"timestamp": _ts(base, 180), "value": 50.0},
            ],
            "query_latency_ms": [
                {"timestamp": _ts(base, -300), "value": 8.0},
                {"timestamp": _ts(base, 180), "value": 12.0},
            ],
        },
    }

    alerts = [
        {"timestamp": _ts(base, 120), "service": "payment-service", "severity": "warning",
         "title": "Connection Pool High Utilization",
         "description": "payment-service DB connection pool at 94% utilization."},
        {"timestamp": _ts(base, 180), "service": "payment-service", "severity": "critical",
         "title": "Connection Pool Exhausted",
         "description": "All 50 DB connections in use. New requests waiting or timing out."},
        {"timestamp": _ts(base, 215), "service": "order-service", "severity": "high",
         "title": "Payment Processing Failures",
         "description": "Multiple orders failing due to payment-service timeouts."},
    ]

    traces = []

    return {
        "scenario_id": "medium_payment_pool_leak",
        "difficulty": "medium",
        "services": services_used,
        "logs": logs,
        "metrics": metrics,
        "alerts": alerts,
        "traces": traces,
        "initial_alert": "CRITICAL: Payment processing failures. Connection pool exhausted on payment-service. Orders failing with 500 errors.",
        "ground_truth": {
            "root_cause": "Database connection pool leak in payment-service's refund_processor.handle_partial_refund() code path - connections acquired but never released",
            "root_cause_service": "payment-service",
            "affected_services": ["payment-service", "order-service", "api-gateway"],
            "severity": "critical",
            "remediation": "1. Restart payment-service to release leaked connections. 2. Fix connection leak in refund_processor.handle_partial_refund() - add proper connection release in finally block. 3. Configure connection pool leak detection with shorter timeout. 4. Add connection pool utilization alerts at 75% threshold.",
            "key_evidence": [
                "DB pool active connections monotonically increasing from 15 to 50",
                "18 connections leaked - acquired but never released",
                "Suspected code path: refund_processor.handle_partial_refund()",
                "payment-db itself is healthy (8-12ms query latency)",
                "Stripe latency blip was transient and recovered",
            ],
        },
    }


# ── Hard Scenarios ──────────────────────────────────────────────────────────

def _hard_scenario_1(seed: int) -> dict[str, Any]:
    """Subtle memory leak + GC pressure in order-service combined with
    intermittent network partitioning — symptoms point toward Kafka and DB
    but root cause is JVM GC stop-the-world pauses in order-service."""
    base = datetime(2025, 3, 19, 3, 0, 0)
    services_used = [
        "api-gateway", "order-service", "order-db", "kafka-broker",
        "inventory-service", "payment-service", "redis-cache",
        "auth-service",
    ]

    logs = [
        # Subtle early warnings buried in noise
        {"timestamp": _ts(base, 0), "service": "order-service", "level": "DEBUG",
         "message": "JVM heap usage: 4.2GB / 8GB (52.5%). GC pause: 45ms (minor)"},
        {"timestamp": _ts(base, 300), "service": "order-service", "level": "DEBUG",
         "message": "JVM heap usage: 5.1GB / 8GB (63.7%). GC pause: 120ms (minor)"},
        {"timestamp": _ts(base, 600), "service": "order-service", "level": "DEBUG",
         "message": "JVM heap usage: 6.3GB / 8GB (78.7%). GC pause: 450ms (major)"},
        {"timestamp": _ts(base, 900), "service": "order-service", "level": "WARNING",
         "message": "JVM heap usage: 7.2GB / 8GB (90.0%). GC pause: 2800ms (full GC)"},
        {"timestamp": _ts(base, 1000), "service": "order-service", "level": "WARNING",
         "message": "JVM heap usage: 7.6GB / 8GB (95.0%). GC pause: 8500ms (full GC). Application threads frozen."},

        # The GC pauses cause Kafka consumer heartbeat failures
        {"timestamp": _ts(base, 905), "service": "kafka-broker", "level": "WARNING",
         "message": "Consumer order-service-consumer-1 heartbeat timeout (session.timeout.ms=10000)"},
        {"timestamp": _ts(base, 910), "service": "kafka-broker", "level": "WARNING",
         "message": "Consumer group 'order-processors' member order-service-consumer-1 left group (heartbeat expired)"},
        {"timestamp": _ts(base, 1010), "service": "kafka-broker", "level": "ERROR",
         "message": "Consumer group 'order-processors' rebalancing: 1 member left, 2 remaining"},

        # GC pauses cause DB connection timeouts — looks like DB is the issue
        {"timestamp": _ts(base, 920), "service": "order-service", "level": "ERROR",
         "message": "Database query timeout after 5000ms: SELECT * FROM orders WHERE id = 'ORD-31500'"},
        {"timestamp": _ts(base, 925), "service": "order-db", "level": "INFO",
         "message": "Query completed in 12ms: SELECT * FROM orders WHERE id = 'ORD-31500' [note: client may have disconnected]"},
        {"timestamp": _ts(base, 1020), "service": "order-service", "level": "ERROR",
         "message": "ConnectionReset: Connection to order-db closed by server (idle timeout during GC pause)"},

        # Red herring: intermittent network blip
        {"timestamp": _ts(base, 800), "service": "api-gateway", "level": "WARNING",
         "message": "TCP retransmission rate elevated: 2.3% on interface eth0"},
        {"timestamp": _ts(base, 850), "service": "api-gateway", "level": "INFO",
         "message": "TCP retransmission rate normalized: 0.1%"},

        # Red herring: redis has routine evictions
        {"timestamp": _ts(base, 500), "service": "redis-cache", "level": "INFO",
         "message": "Evicted 127 keys (LRU). Memory: 3.8GB / 4GB (95%). Normal operation."},
        {"timestamp": _ts(base, 700), "service": "redis-cache", "level": "INFO",
         "message": "Evicted 89 keys (LRU). Memory: 3.7GB / 4GB (92.5%). Normal operation."},

        # auth-service unrelated noise
        {"timestamp": _ts(base, 400), "service": "auth-service", "level": "INFO",
         "message": "JWT rotation completed. New signing key active."},
        {"timestamp": _ts(base, 600), "service": "auth-service", "level": "INFO",
         "message": "Rate limiter: 0 requests throttled in last 5 minutes."},

        # Actual user-visible impact
        {"timestamp": _ts(base, 1050), "service": "api-gateway", "level": "ERROR",
         "message": "POST /api/v1/orders -> order-service (504 Gateway Timeout)"},
        {"timestamp": _ts(base, 1060), "service": "api-gateway", "level": "ERROR",
         "message": "GET /api/v1/orders/ORD-31490 -> order-service (504 Gateway Timeout)"},
        {"timestamp": _ts(base, 1070), "service": "order-service", "level": "ERROR",
         "message": "Thread pool exhaustion: 200/200 threads blocked. Incoming requests rejected."},
        {"timestamp": _ts(base, 1080), "service": "order-service", "level": "CRITICAL",
         "message": "java.lang.OutOfMemoryError: GC overhead limit exceeded. Heap dump written to /tmp/heapdump-20250319-030000.hprof"},

        # Other services are fine
        {"timestamp": _ts(base, 1000), "service": "payment-service", "level": "INFO",
         "message": "Payment processing nominal. Average latency: 180ms. Error rate: 0.02%"},
        {"timestamp": _ts(base, 1000), "service": "inventory-service", "level": "INFO",
         "message": "Inventory sync completed. 0 discrepancies found."},
    ]

    metrics = {
        "order-service": {
            "jvm_heap_usage_percent": [
                {"timestamp": _ts(base, 0), "value": 52.5},
                {"timestamp": _ts(base, 300), "value": 63.7},
                {"timestamp": _ts(base, 600), "value": 78.7},
                {"timestamp": _ts(base, 900), "value": 90.0},
                {"timestamp": _ts(base, 1000), "value": 95.0},
                {"timestamp": _ts(base, 1080), "value": 99.8},
            ],
            "gc_pause_duration_ms": [
                {"timestamp": _ts(base, 0), "value": 45.0},
                {"timestamp": _ts(base, 300), "value": 120.0},
                {"timestamp": _ts(base, 600), "value": 450.0},
                {"timestamp": _ts(base, 900), "value": 2800.0},
                {"timestamp": _ts(base, 1000), "value": 8500.0},
            ],
            "request_latency_p99_ms": [
                {"timestamp": _ts(base, 0), "value": 150.0},
                {"timestamp": _ts(base, 600), "value": 800.0},
                {"timestamp": _ts(base, 900), "value": 5200.0},
                {"timestamp": _ts(base, 1050), "value": 30000.0},
            ],
            "active_threads": [
                {"timestamp": _ts(base, 0), "value": 45.0},
                {"timestamp": _ts(base, 600), "value": 89.0},
                {"timestamp": _ts(base, 900), "value": 156.0},
                {"timestamp": _ts(base, 1070), "value": 200.0},
            ],
        },
        "order-db": {
            "query_latency_ms": [
                {"timestamp": _ts(base, 0), "value": 8.0},
                {"timestamp": _ts(base, 600), "value": 9.0},
                {"timestamp": _ts(base, 1000), "value": 12.0},
            ],
            "connections_active": [
                {"timestamp": _ts(base, 0), "value": 30.0},
                {"timestamp": _ts(base, 900), "value": 45.0},
                {"timestamp": _ts(base, 1020), "value": 18.0},
            ],
        },
        "kafka-broker": {
            "consumer_lag_total": [
                {"timestamp": _ts(base, 0), "value": 5.0},
                {"timestamp": _ts(base, 600), "value": 8.0},
                {"timestamp": _ts(base, 910), "value": 340.0},
                {"timestamp": _ts(base, 1050), "value": 890.0},
            ],
        },
        "api-gateway": {
            "tcp_retransmission_rate": [
                {"timestamp": _ts(base, 0), "value": 0.1},
                {"timestamp": _ts(base, 800), "value": 2.3},
                {"timestamp": _ts(base, 850), "value": 0.1},
                {"timestamp": _ts(base, 1000), "value": 0.15},
            ],
        },
    }

    alerts = [
        {"timestamp": _ts(base, 800), "service": "api-gateway", "severity": "warning",
         "title": "Network Retransmission Spike",
         "description": "TCP retransmission rate elevated to 2.3% on api-gateway."},
        {"timestamp": _ts(base, 910), "service": "kafka-broker", "severity": "high",
         "title": "Consumer Group Member Left",
         "description": "order-service consumer left order-processors group. Consumer lag increasing."},
        {"timestamp": _ts(base, 1020), "service": "order-service", "severity": "high",
         "title": "Database Connection Resets",
         "description": "Multiple connection resets to order-db. Possible connectivity issue."},
        {"timestamp": _ts(base, 1050), "service": "api-gateway", "severity": "critical",
         "title": "Service Unavailable",
         "description": "order-service returning 504 timeouts. Multiple endpoints affected."},
        {"timestamp": _ts(base, 1080), "service": "order-service", "severity": "critical",
         "title": "OutOfMemoryError",
         "description": "JVM OutOfMemoryError: GC overhead limit exceeded. Heap dump generated."},
    ]

    traces = [
        {"trace_id": "tr-020", "span_id": "s-020", "parent_span_id": None,
         "service": "api-gateway", "operation": "POST /api/v1/orders",
         "duration_ms": 30000.0, "status": "TIMEOUT", "timestamp": _ts(base, 1050)},
        {"trace_id": "tr-020", "span_id": "s-021", "parent_span_id": "s-020",
         "service": "order-service", "operation": "createOrder",
         "duration_ms": 29950.0, "status": "TIMEOUT", "timestamp": _ts(base, 1050)},
    ]

    return {
        "scenario_id": "hard_jvm_memory_leak_gc_storm",
        "difficulty": "hard",
        "services": services_used,
        "logs": logs,
        "metrics": metrics,
        "alerts": alerts,
        "traces": traces,
        "initial_alert": "CRITICAL: order-service returning 504 timeouts. Consumer group rebalancing on Kafka. Database connection resets detected. Network retransmission spike observed.",
        "ground_truth": {
            "root_cause": "Memory leak in order-service JVM causing progressive heap exhaustion and increasingly severe GC stop-the-world pauses, which cascade into Kafka consumer heartbeat failures, DB connection timeouts, and eventual thread pool exhaustion",
            "root_cause_service": "order-service",
            "affected_services": ["order-service", "api-gateway", "kafka-broker"],
            "severity": "critical",
            "remediation": "1. Immediately restart order-service to restore availability. 2. Analyze heap dump at /tmp/heapdump-20250319-030000.hprof to identify the leak source. 3. Increase JVM heap size as short-term mitigation. 4. Fix the memory leak in application code. 5. Configure GC pause monitoring alerts at 1000ms threshold. 6. Consider switching to G1GC or ZGC for lower pause times.",
            "key_evidence": [
                "JVM heap monotonically increasing: 52.5% -> 99.8% over ~18 minutes",
                "GC pause durations escalating: 45ms -> 8500ms",
                "order-db query latency remained low (8-12ms) — DB is healthy",
                "Kafka consumer heartbeat failures correlate with GC pauses (>10s session timeout)",
                "Network retransmission spike was transient and unrelated",
                "Redis evictions are routine LRU behavior at normal levels",
                "Final OOM error confirms JVM memory as root cause",
            ],
        },
    }


# ── Scenario Registry ──────────────────────────────────────────────────────

SCENARIO_REGISTRY: dict[str, list] = {
    "easy": [_easy_scenario_1, _easy_scenario_2],
    "medium": [_medium_scenario_1, _medium_scenario_2],
    "hard": [_hard_scenario_1],
}

TASK_DIFFICULTY_MAP: dict[str, str] = {
    "task1_easy": "easy",
    "task2_medium": "medium",
    "task3_hard": "hard",
}


def get_scenario(task_id: str, seed: int | None = None) -> dict[str, Any]:
    """Load a scenario for the given task. Uses seed for deterministic selection."""
    difficulty = TASK_DIFFICULTY_MAP.get(task_id)
    if difficulty is None:
        raise ValueError(f"Unknown task_id: {task_id}")

    generators = SCENARIO_REGISTRY[difficulty]

    if seed is None:
        seed = random.randint(0, 2**31)

    rng = random.Random(seed)
    gen = rng.choice(generators)
    scenario = gen(seed)

    return scenario
