from typing import Dict, Any, Optional
from mcp.server import db_instance

class ArchitectAgent:
    """
    Architect Agent: Performance Planner.
    Analyzes execution plans from the database telemetry layer,
    identifies bottlenecks, and designs precise SQL index fixes.
    """
    def __init__(self):
        pass

    def analyze_slow_query(self, alert_payload: Dict[str, Any], db_instance_override: Optional[Any] = None) -> Dict[str, Any]:
        """
        Receives an alert from the Sentry, pulls the execution plan from the database engine,
        analyzes the plan, and formulates a performance index proposal.
        """
        sql = alert_payload["sql"]
        
        # Pull the live execution plan from the DB engine (simulating an MCP tool call)
        active_db = db_instance_override if db_instance_override is not None else db_instance
        plan_analysis = active_db.explain_query(sql)
        plan_tree = plan_analysis.get("plan_tree", {})
        bottleneck = plan_analysis.get("bottleneck_detected", "No specific bottleneck detected.")
        potential_fix = plan_analysis.get("potential_fix", "")

        # Formulate technical reasoning for the index creation
        def find_seq_scan(node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            if node.get("Node Type") == "Seq Scan":
                return node
            for child in node.get("Plans", []):
                res = find_seq_scan(child)
                if res:
                    return res
            return None

        seq_scan_node = find_seq_scan(plan_tree) or plan_tree
        table_name = seq_scan_node.get("Relation Name", "unknown")
        filter_cond = seq_scan_node.get("Filter", "none")
        node_type = seq_scan_node.get("Node Type", "unknown")
        
        if potential_fix:
            reasoning = (
                f"The database planner is executing a Sequential Scan on table '{table_name}' "
                f"matching filter conditions '{filter_cond}'. For a table of this size, "
                f"this results in high CPU and disk I/O costs. Creating a B-Tree index covering the filter "
                f"columns will allow the planner to perform an Index Scan instead, reducing cost from "
                f"{plan_tree.get('Total Cost', 'N/A')} to less than 10.0."
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
