from typing import Dict, Any
from mcp.server import db_instance

class ArchitectAgent:
    """
    Architect Agent: Performance Planner.
    Analyzes execution plans from the database telemetry layer,
    identifies bottlenecks, and designs precise SQL index fixes.
    """
    def __init__(self):
        pass

    def analyze_slow_query(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receives an alert from the Sentry, pulls the execution plan from the database engine,
        analyzes the plan, and formulates a performance index proposal.
        """
        sql = alert_payload["sql"]
        
        # Pull the live execution plan from the DB engine (simulating an MCP tool call)
        plan_analysis = db_instance.explain_query(sql)
        plan_tree = plan_analysis.get("plan_tree", {})
        bottleneck = plan_analysis.get("bottleneck_detected", "No specific bottleneck detected.")
        potential_fix = plan_analysis.get("potential_fix", "")

        # Formulate technical reasoning for the index creation
        table_name = plan_tree.get("Relation Name", "unknown")
        filter_cond = plan_tree.get("Filter", "none")
        node_type = plan_tree.get("Node Type", "unknown")
        
        if node_type == "Seq Scan" and potential_fix:
            reasoning = (
                f"The database planner is executing a Sequential Scan on table '{table_name}' "
                f"matching filter conditions '{filter_cond}'. For a table of this size, "
                f"this results in high CPU and disk I/O costs. Creating a B-Tree index covering the filter "
                f"columns will allow the planner to perform an Index Scan instead, reducing cost from "
                f"{plan_tree.get('Total Cost')} to less than 10.0."
            )
        else:
            reasoning = "Query execution plan is already optimized or no index optimization is applicable."
            potential_fix = ""

        proposal = {
            "query_id": alert_payload["query_id"],
            "original_query": sql,
            "execution_time_ms": alert_payload["execution_time_ms"],
            "execution_plan": plan_tree,
            "bottleneck": bottleneck,
            "proposed_sql": potential_fix,
            "reasoning": reasoning,
            "status": "Awaiting Safety Clearance"
        }
        return proposal
