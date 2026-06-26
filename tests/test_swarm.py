import unittest
from mcp.server import db_instance, MockPostgreSQLDatabase
from agents.sentry import SentryAgent
from agents.architect import ArchitectAgent
from agents.security_guard import SecurityGuardAgent

class TestSQLOptimizationSwarm(unittest.TestCase):
    def setUp(self):
        # Create a fresh database instance for isolated testing
        self.db = MockPostgreSQLDatabase()
        self.sentry = SentryAgent(latency_threshold_ms=100.0)
        self.architect = ArchitectAgent()
        self.security_guard = SecurityGuardAgent()

    def test_sentry_intercepts_slow_query(self):
        """
        Verify that the Sentry agent correctly flags slow queries
        while ignoring fast queries.
        """
        fast_log = {
            "query_id": "q_000001",
            "sql": "SELECT * FROM users WHERE id = 42;",
            "execution_time_ms": 0.45,
            "timestamp": 123456789.0
        }
        slow_log = {
            "query_id": "q_000002",
            "sql": "SELECT * FROM users WHERE email = 'test@example.com';",
            "execution_time_ms": 485.20,
            "timestamp": 123456789.0
        }

        # Fast query should not generate an alert
        fast_alert = self.sentry.analyze_log_entry(fast_log)
        self.assertIsNone(fast_alert)

        # Slow query should trigger a critical or warning alert
        slow_alert = self.sentry.analyze_log_entry(slow_log)
        self.assertIsNotNone(slow_alert)
        self.assertEqual(slow_alert["query_id"], "q_000002")
        self.assertEqual(slow_alert["sql"], slow_log["sql"])
        self.assertEqual(slow_alert["execution_time_ms"], 485.20)

    def test_architect_creates_valid_index_proposal(self):
        """
        Verify that the Architect Agent correctly identifies bottlenecks
        from execution plans and designs a precise index fix.
        """
        alert = {
            "query_id": "q_000002",
            "sql": "SELECT * FROM users WHERE email = 'test@example.com';",
            "execution_time_ms": 485.20
        }
        
        proposal = self.architect.analyze_slow_query(alert)
        self.assertEqual(proposal["query_id"], "q_000002")
        self.assertIn("CREATE INDEX CONCURRENTLY", proposal["proposed_sql"])
        self.assertIn("users", proposal["proposed_sql"])
        self.assertIn("email", proposal["proposed_sql"])
        self.assertIn("Seq Scan", proposal["execution_plan"]["Node Type"])

    def test_security_guard_approves_safe_proposal(self):
        """
        Verify that the Security Guard Agent approves a standard
        concurrent index creation proposal.
        """
        proposal = {
            "query_id": "q_000002",
            "original_query": "SELECT * FROM users WHERE email = 'test@example.com';",
            "proposed_sql": "CREATE INDEX CONCURRENTLY idx_users_email ON users (email);",
            "execution_time_ms": 485.20
        }
        
        report = self.security_guard.validate_proposal(proposal)
        self.assertTrue(report["approved"])
        self.assertFalse(report["violation_detected"])
        self.assertIsNone(report["violation_details"])

    def test_security_guard_rejects_non_concurrent_index(self):
        """
        Verify that the Security Guard Agent rejects an index creation
        proposal that does not use the CONCURRENTLY keyword (which would lock the table).
        """
        proposal = {
            "query_id": "q_000002",
            "original_query": "SELECT * FROM users WHERE email = 'test@example.com';",
            "proposed_sql": "CREATE INDEX idx_users_email ON users (email);",
            "execution_time_ms": 485.20
        }
        
        report = self.security_guard.validate_proposal(proposal)
        self.assertFalse(report["approved"])
        self.assertTrue(report["violation_detected"])
        self.assertIn("CONCURRENTLY", report["reason"])

    def test_security_guard_blocks_destructive_queries(self):
        """
        Verify that the Security Guard Agent rigorously intercepts
        and rejects destructive queries (such as DROP TABLE, SQL injections, or stacked commands).
        """
        # Test case 1: Stacked Query / Command Injection
        proposal_stacked = {
            "query_id": "q_000003",
            "original_query": "SELECT * FROM users WHERE email = 'test@example.com';",
            "proposed_sql": "CREATE INDEX CONCURRENTLY idx_users_email ON users (email); DROP TABLE users;",
            "execution_time_ms": 485.20
        }
        report = self.security_guard.validate_proposal(proposal_stacked)
        self.assertFalse(report["approved"])
        self.assertTrue(report["violation_detected"])
        self.assertIn("stacked queries", report["violation_details"].lower())

        # Test case 2: Blacklisted Keyword 'DROP'
        proposal_drop = {
            "query_id": "q_000004",
            "original_query": "SELECT * FROM users WHERE email = 'test@example.com';",
            "proposed_sql": "DROP TABLE users;",
            "execution_time_ms": 485.20
        }
        report = self.security_guard.validate_proposal(proposal_drop)
        self.assertFalse(report["approved"])
        self.assertTrue(report["violation_detected"])
        self.assertIn("prohibited sql keyword", report["violation_details"].lower())

        # Test case 3: Blacklisted Keyword 'DELETE'
        proposal_delete = {
            "query_id": "q_000005",
            "original_query": "SELECT * FROM users WHERE email = 'test@example.com';",
            "proposed_sql": "DELETE FROM users WHERE id = 12;",
            "execution_time_ms": 485.20
        }
        report = self.security_guard.validate_proposal(proposal_delete)
        self.assertFalse(report["approved"])
        self.assertTrue(report["violation_detected"])
        self.assertIn("delete", report["violation_details"].lower())

    def test_end_to_end_optimization_loop(self):
        """
        Tests the full pipeline: unindexed query is slow -> index applied -> query becomes fast.
        """
        query = "SELECT * FROM users WHERE email = 'user_123@gmail.com';"
        
        # 1. Initial State: No index exists, execution plan is a Seq Scan (slow)
        initial_explain = db_instance.explain_query(query)
        self.assertEqual(initial_explain["plan_tree"]["Node Type"], "Seq Scan")
        self.assertGreater(initial_explain["execution_time_ms"], 100.0)

        # 2. Architect proposes index
        alert = {
            "query_id": "q_test",
            "sql": query,
            "execution_time_ms": initial_explain["execution_time_ms"]
        }
        proposal = self.architect.analyze_slow_query(alert)
        self.assertIn("CREATE INDEX CONCURRENTLY", proposal["proposed_sql"])

        # 3. Security Guard approves
        report = self.security_guard.validate_proposal(proposal)
        self.assertTrue(report["approved"])

        # 4. Execute optimization DDL on the database
        exec_result = db_instance.execute_ddl(proposal["proposed_sql"])
        self.assertTrue(exec_result["success"])

        # 5. Optimized State: Index now exists, execution plan is an Index Scan (fast!)
        post_explain = db_instance.explain_query(query)
        self.assertEqual(post_explain["plan_tree"]["Node Type"], "Index Scan")
        self.assertEqual(post_explain["plan_tree"]["Index Name"], "idx_users_email")
        self.assertLess(post_explain["execution_time_ms"], 5.0)

if __name__ == "__main__":
    unittest.main()
