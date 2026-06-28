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

    def get_active_queries(self) -> List[Dict[str, Any]]:
        """Stub for mock database to match RealPostgreSQLDatabase interface."""
        return []

    def cancel_query(self, pid: int) -> bool:
        """Stub for mock database to match RealPostgreSQLDatabase interface."""
        return True

    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Simulates query execution on mock database and returns structured results for SELECTs."""
        sql_clean = sql_query.strip().lower()
        if "select" in sql_clean:
            parsed = self.parse_query_target(sql_query)
            table = parsed["table"]
            if table in self.tables:
                columns = self.tables[table]["columns"]
                import random
                rows = []
                for i in range(1, 6):
                    row = []
                    for col in columns:
                        if col == "id":
                            row.append(i)
                        elif col == "email":
                            row.append(f"user_{random.randint(100, 999)}@gmail.com")
                        elif col == "created_at":
                            row.append("2026-06-28 12:00:00")
                        elif col == "status":
                            row.append("active")
                        elif col == "user_id":
                            row.append(random.randint(1, 100))
                        elif col == "total":
                            row.append(round(random.uniform(10.0, 500.0), 2))
                        elif col == "order_id":
                            row.append(random.randint(1, 100))
                        elif col == "amount":
                            row.append(round(random.uniform(5.0, 200.0), 2))
                        elif col == "payment_method":
                            row.append(random.choice(["credit_card", "paypal", "apple_pay", "stripe"]))
                        else:
                            row.append("mock_val")
                    rows.append(row)
                return {
                    "success": True,
                    "is_select": True,
                    "columns": columns,
                    "rows": rows
                }
        return {
            "success": True,
            "is_select": False,
            "message": "Query executed successfully on mock database (No-op)."
        }


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

class RealPostgreSQLDatabase:
    """
    A database operations adapter that connects in real-time to a live
    PostgreSQL database. It dynamically queries catalog metadata for tables,
    indexes, and column sizes, runs real EXPLAIN plans, and executes index DDL commands.
    """
    def __init__(self, connection_uri: str):
        import psycopg2
        import psycopg2.extras
        self.connection_uri = connection_uri
        # Connect to the real database
        self.conn = psycopg2.connect(connection_uri)
        # Enable autocommit so DDLs like CREATE INDEX CONCURRENTLY can execute
        self.conn.autocommit = True
        self.executed_optimizations: List[Dict[str, Any]] = []
        
        # Ensure our tables exist for the telemetry generator
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Checks if schema tables users, orders, transactions exist. If not, creates and seeds them."""
        cursor = self.conn.cursor()
        try:
            # Check for users table
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'users');")
            users_exists = cursor.fetchone()[0]
            
            # Check for orders table
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'orders');")
            orders_exists = cursor.fetchone()[0]
            
            # Check for transactions table
            cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'transactions');")
            transactions_exists = cursor.fetchone()[0]
            
            if not users_exists:
                cursor.execute("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        status VARCHAR(50) DEFAULT 'active'
                    );
                """)
                # Insert mock users in a single multi-row batch
                values_str = ",".join(f"('user_{i}@gmail.com', 'active')" for i in range(1, 2001))
                cursor.execute(f"INSERT INTO users (email, status) VALUES {values_str};")
                
            if not orders_exists:
                cursor.execute("""
                    CREATE TABLE orders (
                        id SERIAL PRIMARY KEY,
                        user_id INT,
                        total NUMERIC(10, 2),
                        created_at TIMESTAMP DEFAULT NOW(),
                        status VARCHAR(50) DEFAULT 'pending'
                    );
                """)
                # Insert mock orders in a single multi-row batch
                values_str = ",".join(f"({i % 1500 + 1}, {round(i * 1.5, 2)}, 'pending')" for i in range(1, 4001))
                cursor.execute(f"INSERT INTO orders (user_id, total, status) VALUES {values_str};")
                
            if not transactions_exists:
                cursor.execute("""
                    CREATE TABLE transactions (
                        id SERIAL PRIMARY KEY,
                        order_id INT,
                        amount NUMERIC(10, 2),
                        payment_method VARCHAR(50),
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                # Insert mock transactions in a single multi-row batch
                methods = ["credit_card", "paypal", "apple_pay", "stripe"]
                values_str = ",".join(f"({i % 3500 + 1}, {round(i * 1.1, 2)}, '{methods[i % 4]}')" for i in range(1, 5001))
                cursor.execute(f"INSERT INTO transactions (order_id, amount, payment_method) VALUES {values_str};")
                
            # If any table was created, run ANALYZE to update pg_stat_user_tables row counts immediately
            if not (users_exists and orders_exists and transactions_exists):
                cursor.execute("ANALYZE users; ANALYZE orders; ANALYZE transactions;")
                
            cursor.close()
        except Exception as e:
            if not cursor.closed:
                cursor.close()
            # Suppress/log database setup exceptions
            print(f"Error checking/creating tables: {e}")


    def get_existing_indexes(self) -> List[Dict[str, Any]]:
        """Queries pg_indexes to fetch active indexes in the public schema."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT indexname, tablename, indexdef 
                FROM pg_indexes 
                WHERE schemaname = 'public';
            """)
            rows = cursor.fetchall()
            cursor.close()
            
            indexes = []
            for row in rows:
                name, table, definition = row
                # Simple parsing of columns from indexdef: e.g., ON table (col1, col2)
                cols = []
                col_match = re.search(r"\((.*?)\)", definition)
                if col_match:
                    cols = [c.strip().strip('"') for c in col_match.group(1).split(",")]
                indexes.append({
                    "name": name,
                    "table": table,
                    "columns": cols
                })
            return indexes
        except Exception as e:
            if not cursor.closed:
                cursor.close()
            # Return empty on error
            return []

    @property
    def tables(self) -> Dict[str, Any]:
        """
        Queries information_schema and pg_stat_user_tables 
        to dynamically return real table schema and live row counts.
        """
        cursor = self.conn.cursor()
        try:
            # 1. Fetch tables and columns
            cursor.execute("""
                SELECT table_name, column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                ORDER BY table_name, ordinal_position;
            """)
            col_rows = cursor.fetchall()
            
            # 2. Fetch row counts
            cursor.execute("""
                SELECT relname AS table_name, n_live_tup AS rows_count 
                FROM pg_stat_user_tables;
            """)
            count_rows = cursor.fetchall()
            cursor.close()
            
            row_counts = {r[0]: max(0, r[1]) for r in count_rows}
            
            tables_schema = {}
            for row in col_rows:
                table_name, col_name = row
                if table_name not in tables_schema:
                    tables_schema[table_name] = {
                        "columns": [],
                        "rows_count": row_counts.get(table_name, 0)
                    }
                tables_schema[table_name]["columns"].append(col_name)
            return tables_schema
        except Exception as e:
            if not cursor.closed:
                cursor.close()
            return {}

    def parse_query_target(self, query: str) -> Dict[str, Any]:
        """
        Extracts table and columns from SQL query templates
        by matching against real tables and columns.
        """
        query_clean = query.strip().replace("\n", " ").lower()
        result = {"table": "unknown", "columns": [], "type": "unknown"}
        
        real_tables = self.tables
        
        if query_clean.startswith("select") or "select " in query_clean:
            result["type"] = "select"
            # Identify the main table from real tables
            for table in real_tables.keys():
                if f"from {table}" in query_clean or f"join {table}" in query_clean:
                    result["table"] = table
                    break
            
            # Simple column extraction from WHERE/JOIN clauses based on table columns
            if result["table"] != "unknown":
                table_cols = real_tables[result["table"]]["columns"]
                for col in table_cols:
                    # Check if column is in the query (with word boundary to avoid partial match)
                    if re.search(rf"\b{col}\b", query_clean):
                        # Avoid adding PK 'id' as the main filter column if possible
                        if col != "id" or not result["columns"]:
                            result["columns"].append(col)
                            
        return result

    def explain_query(self, query: str) -> Dict[str, Any]:
        """
        Executes a real EXPLAIN (FORMAT JSON) on the connected database.
        Parses the JSON result to detect bottlenecks and build optimization proposals.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
            explain_result = cursor.fetchone()
            cursor.close()
            
            if not explain_result or not explain_result[0]:
                return {
                    "query": query,
                    "execution_time_ms": 0.0,
                    "plan_tree": {},
                    "bottleneck_detected": "Failed to retrieve explain plan.",
                    "potential_fix": "None."
                }
                
            plan_data = explain_result[0][0] # JSON output from explain
            plan_tree = plan_data.get("Plan", {})
            
            total_cost = plan_tree.get("Total Cost", 0.0)
            startup_cost = plan_tree.get("Startup Cost", 0.0)
            plan_rows = plan_tree.get("Plan Rows", 0)
            
            # Identify sequential scans on tables
            bottleneck = "None. Query is fully optimized."
            potential_fix = "None needed."
            
            def find_bottlenecks(node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                node_type = node.get("Node Type", "")
                relation = node.get("Relation Name", "")
                
                # A Seq Scan on a table with > 1000 rows is a bottleneck
                if node_type == "Seq Scan" and relation:
                    tables_schema = self.tables
                    rows = tables_schema.get(relation, {}).get("rows_count", 0)
                    if rows > 1000:
                        # Extract filter columns if present
                        filter_cond = node.get("Filter", "")
                        columns = []
                        if filter_cond:
                            for c in filter_cond.replace("(", "").replace(")", "").replace("'", "").split("="):
                                c_clean = c.strip().split(".")[-1] # strip table alias
                                if c_clean in tables_schema.get(relation, {}).get("columns", []):
                                    columns.append(c_clean)
                        return {
                            "table": relation,
                            "columns": columns
                        }
                        
                for child in node.get("Plans", []):
                    res = find_bottlenecks(child)
                    if res:
                        return res
                return None
                
            bt = find_bottlenecks(plan_tree)
            
            if bt and bt["table"] != "unknown":
                table = bt["table"]
                columns = bt["columns"]
                if not columns:
                    parsed = self.parse_query_target(query)
                    if parsed["table"] == table:
                        columns = parsed["columns"]
                
                if not columns:
                    columns = ["id"]
                    
                bottleneck = f"Sequential Scan on relation '{table}' due to missing index."
                cols_str = ", ".join(columns)
                potential_fix = f"CREATE INDEX CONCURRENTLY idx_{table}_{'_'.join(columns)} ON {table} ({cols_str});"
                execution_time = 150.0 + (total_cost / 10.0)
            else:
                execution_time = 0.5 + (total_cost / 100.0)
                
            return {
                "query": query,
                "execution_time_ms": round(execution_time, 2),
                "plan_tree": plan_tree,
                "bottleneck_detected": bottleneck,
                "potential_fix": potential_fix
            }
        except Exception as e:
            if not cursor.closed:
                cursor.close()
            return {
                "query": query,
                "execution_time_ms": 0.0,
                "plan_tree": {},
                "bottleneck_detected": f"Error running explain: {str(e)}",
                "potential_fix": "None."
            }

    def execute_ddl(self, sql_command: str) -> Dict[str, Any]:
        """Executes the DDL command directly on the active PostgreSQL database."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql_command)
            cursor.close()
            
            log_entry = {
                "sql": sql_command,
                "status": "Applied Successfully"
            }
            self.executed_optimizations.append(log_entry)
            
            return {
                "success": True,
                "message": "DDL statement executed successfully on the active database.",
                "details": log_entry
            }
        except Exception as e:
            if not cursor.closed:
                cursor.close()
            return {
                "success": False,
                "error": f"Failed to execute DDL: {str(e)}"
            }

    def get_active_queries(self) -> List[Dict[str, Any]]:
        """Queries pg_stat_activity to find currently running queries in public schema."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT pid, query, state, extract(epoch from (now() - query_start)) * 1000 AS duration_ms
                FROM pg_stat_activity
                WHERE state = 'active'
                  AND query NOT LIKE '%pg_stat_activity%'
                  AND query NOT LIKE '%pg_stat_statements%'
                  AND query NOT LIKE '%SELECT EXISTS%'
                  AND query NOT LIKE '%information_schema%'
                  AND query != ''
                  AND query IS NOT NULL
                  AND usename != 'rdsadmin'
                  AND pid != pg_backend_pid();
            """)
            rows = cursor.fetchall()
            cursor.close()
            
            queries = []
            for row in rows:
                pid, query_text, state, duration_ms = row
                queries.append({
                    "pid": pid,
                    "query": query_text,
                    "state": state,
                    "duration_ms": duration_ms or 0.0
                })
            return queries
        except Exception as e:
            if not cursor.closed:
                cursor.close()
            return []

    def cancel_query(self, pid: int) -> bool:
        """Cancels a running backend query using pg_cancel_backend."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT pg_cancel_backend(%s);", (pid,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else False
        except Exception as e:
            if not cursor.closed:
                cursor.close()
            return False

    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Executes a query and returns columns and rows (safely limit to 100 rows)."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql_query)
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchmany(100)
                cursor.close()
                return {
                    "success": True,
                    "is_select": True,
                    "columns": columns,
                    "rows": rows
                }
            else:
                cursor.close()
                return {
                    "success": True,
                    "is_select": False,
                    "message": "Query executed successfully, no rows returned."
                }
        except Exception as e:
            if not cursor.closed:
                cursor.close()
            return {
                "success": False,
                "error": str(e)
            }

    def close(self):
        """Closes the active database connection."""
        try:
            self.conn.close()
        except:
            pass

# Singleton DB Server Instance for telemetry simulation
db_instance = MockPostgreSQLDatabase()

