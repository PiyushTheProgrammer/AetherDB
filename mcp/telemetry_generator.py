import random
import time
from typing import Dict, Any, Generator
from mcp.server import db_instance

class TelemetryGenerator:
    """
    Generates a stream of database query executions with real-time performance telemetry.
    The execution time and plan adapt dynamically as indexes are created/removed on the DB instance.
    """
    def __init__(self):
        self.query_counter = 0

    def generate_query_stream(self, db_instance_override=None) -> Generator[Dict[str, Any], None, None]:
        """
        Continuously yields query execution logs containing:
        - Query ID
        - SQL text
        - Execution Time (ms)
        - Timestamp
        - Database Plan details (queried from the mock or real database engine)
        """
        active_db = db_instance_override if db_instance_override is not None else db_instance

        templates_fast = [
            "SELECT * FROM users WHERE id = {id};",
            "SELECT * FROM orders WHERE id = {id};",
            "SELECT * FROM transactions WHERE id = {id};"
        ]

        templates_slow = [
            "SELECT * FROM users WHERE email = 'user_{val}@gmail.com';",
            "SELECT * FROM orders WHERE user_id = {id} ORDER BY created_at DESC;",
            "SELECT * FROM transactions WHERE created_at >= '{date}' AND payment_method = '{method}';",
            "SELECT * FROM users JOIN orders ON users.id = orders.user_id WHERE users.status = 'active';"
        ]

        templates_unsafe = [
            "DROP TABLE transactions;",
            "SELECT * FROM users; DROP TABLE orders;",
            "DELETE FROM users WHERE status = 'suspended';",
            "SELECT * FROM orders; ALTER TABLE orders DROP COLUMN total;",
            "CREATE INDEX idx_users_email ON users (email);",
            "UPDATE transactions SET amount = 0.0 WHERE id = {id};"
        ]

        payment_methods = ["credit_card", "paypal", "apple_pay", "stripe"]
        statuses = ["active", "suspended", "pending"]

        while True:
            self.query_counter += 1
            timestamp = time.time()
            
            # 65% chance of fast query, 30% chance of slow, 5% chance of unsafe query
            rand_val = random.random()
            
            if rand_val < 0.05:
                template = random.choice(templates_unsafe)
                val_id = random.randint(1, 50000)
                sql = template.format(id=val_id)
            elif rand_val < 0.35:
                template = random.choice(templates_slow)
                val_id = random.randint(1000, 99999)
                val_date = f"2026-06-{random.randint(1, 26):02d}"
                val_method = random.choice(payment_methods)
                sql = template.format(id=val_id, val=val_id, date=val_date, method=val_method)
            else:
                template = random.choice(templates_fast)
                val_id = random.randint(1, 50000)
                sql = template.format(id=val_id)


            # Analyze query via our active DB server instance to get live execution metrics
            analysis = active_db.explain_query(sql)
            
            # Build the query log payload
            yield {
                "query_id": f"q_{self.query_counter:06d}",
                "timestamp": timestamp,
                "sql": sql,
                "execution_time_ms": analysis["execution_time_ms"],
                "plan": analysis["plan_tree"],
                "bottleneck": analysis["bottleneck_detected"],
                "potential_fix": analysis["potential_fix"],
                "status": "SLOW" if analysis["execution_time_ms"] > 100.0 else "OK"
            }
            
            # Small random sleep to simulate network stream spacing
            time.sleep(0.5)
