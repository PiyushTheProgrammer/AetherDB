import re
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

# Models for the MCP interface
class QueryPlanNode(BaseModel):
    node_type: str
    relation_name: Optional[str] = None
    alias: Optional[str] = None
    startup_cost: float
    total_cost: float
    plan_rows: int
    plan_width: int
    index_name: Optional[str] = None
    index_cond: Optional[str] = None
    filter_cond: Optional[str] = None

class QueryPlan(BaseModel):
    query: str
    execution_time_ms: float
    plan_tree: Dict[str, Any]
    bottleneck_detected: str
    potential_fix: str

class SafetyValidationResult(BaseModel):
    approved: bool
    reason: str
    violation_details: Optional[str] = None

class MockPostgreSQLDatabase:
    """
    A simulated PostgreSQL Database state tracker that manages mock tables,
    existing indexes, and provides an engine to analyze queries and run optimizations.
    """
    def __init__(self):
        # In-memory mock schema
        self.tables = {
            "users": {
                "columns": ["id", "email", "created_at", "status"],
                "rows_count": 500000
            },
            "orders": {
                "columns": ["id", "user_id", "total", "created_at", "status"],
                "rows_count": 2000000
            },
            "transactions": {
                "columns": ["id", "order_id", "amount", "payment_method", "created_at"],
                "rows_count": 5000000
            }
        }
        
        # Initial active indexes (typically Primary Keys only)
        self.active_indexes = {
            "idx_users_id": {"table": "users", "columns": ["id"]},
            "idx_orders_id": {"table": "orders", "columns": ["id"]},
            "idx_transactions_id": {"table": "transactions", "columns": ["id"]}
        }
        
        # Track history of executed queries
        self.executed_optimizations: List[Dict[str, Any]] = []

    def get_existing_indexes(self) -> List[Dict[str, Any]]:
        """Returns list of currently active indexes."""
        return [
            {"name": name, "table": val["table"], "columns": val["columns"]}
            for name, val in self.active_indexes.items()
        ]

    def parse_query_target(self, query: str) -> Dict[str, Any]:
        """
        Extracts table and columns from simple SQL query templates
        to simulate realistic query plan mapping.
        """
        query_clean = query.strip().replace("\n", " ").lower()
        
        # Default fallback
        result = {"table": "unknown", "columns": [], "type": "unknown"}
        
        # Identify SELECT queries
        if query_clean.startswith("select"):
            result["type"] = "select"
            
            # Simple table name matching
            for table in self.tables.keys():
                if f"from {table}" in query_clean:
                    result["table"] = table
                    break
            
            # Simple column extraction from WHERE/JOIN clauses
            where_match = re.search(r"where\s+(.*)", query_clean)
            if where_match:
                where_clause = where_match.group(1)
                # Find column comparisons like email = ..., user_id = ..., status = ...
                for col in self.tables.get(result["table"], {}).get("columns", []):
                    if col in where_clause:
                        result["columns"].append(col)
            
            # Simple join detection
            join_match = re.search(r"join\s+(\w+)\s+on\s+([\w\.]+)\s*=\s*([\w\.]+)", query_clean)
            if join_match:
                joined_table = join_match.group(1)
                if joined_table in self.tables:
                    # Also record join columns
                    on_clause = join_match.group(2) + " " + join_match.group(3)
                    for col in self.tables.get(joined_table, {}).get("columns", []):
                        if col in on_clause and col not in result["columns"]:
                            result["columns"].append(col)
                            
        return result

    def explain_query(self, query: str) -> Dict[str, Any]:
        """
        Simulates running EXPLAIN (FORMAT JSON) on the target query.
        If an index exists on the filter/join columns, it returns an Index Scan plan.
        Otherwise, it returns a high-cost Sequential Scan plan.
        """
        parsed = self.parse_query_target(query)
        table = parsed["table"]
        columns = parsed["columns"]
        
        if table == "unknown" or not columns:
            return {
                "Plan": {
                    "Node Type": "Result",
                    "Startup Cost": 0.00,
                    "Total Cost": 0.01,
                    "Plan Rows": 1,
                    "Plan Width": 0,
                    "Output": ["Unknown table or parameters"]
                }
            }

        # Check if any index covers the filtered columns
        matching_index = None
        for idx_name, idx_info in self.active_indexes.items():
            if idx_info["table"] == table:
                # Check if the filtered columns match the index columns
                if all(col in idx_info["columns"] for col in columns) or any(col in idx_info["columns"] for col in columns):
                    matching_index = idx_name
                    break

        table_rows = self.tables[table]["rows_count"]
        
        if matching_index:
            # Simulated Index Scan (low cost, fast)
            plan = {
                "Node Type": "Index Scan",
                "Parent Relationship": "Outer",
                "Scan Direction": "Forward",
                "Index Name": matching_index,
                "Relation Name": table,
                "Alias": table,
                "Startup Cost": 0.28,
                "Total Cost": 8.30,
                "Plan Rows": 1,
                "Plan Width": 128,
                "Index Cond": f"({', '.join(columns)} = ?)",
                "Filter": None
            }
            execution_time = 0.85 # milliseconds
            bottleneck = "None. Query optimized using index."
            potential_fix = "None needed."
        else:
            # Simulated Sequential Scan (high cost, slow)
            plan = {
                "Node Type": "Seq Scan",
                "Parent Relationship": "Outer",
                "Relation Name": table,
                "Alias": table,
                "Startup Cost": 0.00,
                "Total Cost": float(table_rows) / 100.0,
                "Plan Rows": int(table_rows * 0.01), # estimated 1% selectivity
                "Plan Width": 128,
                "Filter": f"({', '.join(columns)} = ?)"
            }
            execution_time = 450.0 + (table_rows / 10000.0) # simulated slow latency
            bottleneck = f"Sequential Scan on relation '{table}' covers {table_rows} rows due to missing index."
            cols_str = ", ".join(columns)
            potential_fix = f"CREATE INDEX CONCURRENTLY idx_{table}_{'_'.join(columns)} ON {table} ({cols_str});"

        return {
            "query": query,
            "execution_time_ms": round(execution_time, 2),
            "plan_tree": plan,
            "bottleneck_detected": bottleneck,
            "potential_fix": potential_fix
        }

    def execute_ddl(self, sql_command: str) -> Dict[str, Any]:
        """
        Executes an approved DDL optimization statement, such as CREATE INDEX.
        Updates the internal index registry to simulate state persistence.
        """
        sql_clean = sql_command.strip().replace("\n", " ")
        
        # Regex to parse CREATE INDEX
        # Supports: CREATE INDEX idx_name ON tbl_name (col1, col2)
        # Also supports CONCURRENTLY and UNIQUE keywords
        pattern = re.compile(
            r"create\s+(unique\s+)?index\s+(concurrently\s+)?(\w+)\s+on\s+(\w+)\s*\(\s*([\w\s,]+)\s*\)",
            re.IGNORECASE
        )
        
        match = pattern.search(sql_clean)
        if match:
            _, _, idx_name, table, cols_str = match.groups()
            idx_name = idx_name.lower()
            table = table.lower()
            columns = [c.strip().lower() for c in cols_str.split(",")]
            
            if table not in self.tables:
                return {
                    "success": False,
                    "error": f"Table '{table}' does not exist in schema."
                }
                
            if idx_name in self.active_indexes:
                return {
                    "success": False,
                    "error": f"Index '{idx_name}' already exists."
                }
                
            # Update schema index state
            self.active_indexes[idx_name] = {
                "table": table,
                "columns": columns
            }
            
            log_entry = {
                "sql": sql_command,
                "index_name": idx_name,
                "table": table,
                "columns": columns,
                "status": "Applied Successfully"
            }
            self.executed_optimizations.append(log_entry)
            
            return {
                "success": True,
                "message": f"Successfully created index '{idx_name}' on table '{table}({cols_str})'.",
                "details": log_entry
            }
            
        # Reject non-CREATE INDEX statements
        return {
            "success": False,
            "error": "Only CREATE INDEX operations are permitted through this interface."
        }

# Singleton DB Server Instance for telemetry simulation
db_instance = MockPostgreSQLDatabase()
