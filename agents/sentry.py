from typing import Dict, Any, Optional

class SentryAgent:
    """
    Sentry Agent: Monitored telemetry coordinator.
    Scans incoming database execution logs, intercepts queries that run slower
    than the safety threshold, and alerts the Architect agent.
    """
    def __init__(self, latency_threshold_ms: float = 100.0):
        self.latency_threshold_ms = latency_threshold_ms
        self.total_queries_scanned = 0
        self.slow_queries_intercepted = 0

    def analyze_log_entry(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Scans an individual query log entry.
        Returns an alert payload if the query is classified as slow and requires attention.
        """
        self.total_queries_scanned += 1
        
        execution_time = log_entry.get("execution_time_ms", 0.0)
        
        if execution_time > self.latency_threshold_ms:
            self.slow_queries_intercepted += 1
            
            # Formulate alert details for the swarm
            alert = {
                "alert_id": f"alert_{self.slow_queries_intercepted:04d}",
                "query_id": log_entry.get("query_id"),
                "sql": log_entry.get("sql"),
                "execution_time_ms": execution_time,
                "timestamp": log_entry.get("timestamp"),
                "severity": "CRITICAL" if execution_time > 500.0 else "WARNING",
                "status": "Awaiting Swarm Analysis"
            }
            return alert
            
        return None
