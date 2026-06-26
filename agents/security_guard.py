import re
from typing import Dict, Any, Tuple

class SecurityGuardAgent:
    """
    Security Guard Agent: Safety Gatekeeper.
    Applies strict validation rules derived from skills/security_guard/SKILL.md
    to intercept and reject destructive or unsafe SQL commands.
    """
    def __init__(self):
        # Blacklisted SQL keywords that are strictly prohibited in the swarm
        self.blacklist_keywords = [
            r"\bdrop\b",
            r"\bdelete\b",
            r"\btruncate\b",
            r"\binsert\b",
            r"\bupdate\b",
            r"\breplace\b",
            r"\bgrant\b",
            r"\brevoke\b"
        ]

    def validate_proposal(self, proposal_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the proposed SQL index modification and the original query.
        Returns a structured safety clearance report.
        """
        proposed_sql = proposal_payload.get("proposed_sql", "")
        original_query = proposal_payload.get("original_query", "")

        if not proposed_sql:
            return {
                "approved": False,
                "reason": "No optimization SQL was proposed by the Architect.",
                "violation_detected": True,
                "violation_details": "Proposed SQL is empty."
            }

        # 1. Audit original query for basic safety (read-only queries only)
        original_safe, original_err = self._check_query_safety(original_query, is_proposal=False)
        if not original_safe:
            return {
                "approved": False,
                "reason": "The original query failed safety validation. Potential malicious injection detected.",
                "violation_detected": True,
                "violation_details": original_err
            }

        # 2. Audit proposed SQL optimization
        proposed_safe, proposed_err = self._check_query_safety(proposed_sql, is_proposal=True)
        if not proposed_safe:
            return {
                "approved": False,
                "reason": "The proposed index optimization SQL failed safety validation. Operation rejected.",
                "violation_detected": True,
                "violation_details": proposed_err
            }

        # 3. Check for specific concurrency best-practice
        proposed_clean = proposed_sql.strip().lower()
        if "create index" in proposed_clean and "concurrently" not in proposed_clean:
            return {
                "approved": False,
                "reason": "Index creation must use the CONCURRENTLY keyword to prevent locking the database table.",
                "violation_detected": True,
                "violation_details": "Missing 'CONCURRENTLY' keyword in CREATE INDEX statement."
            }

        # 4. Check that the command is strictly CREATE INDEX or ANALYZE
        allowed_prefix = (
            proposed_clean.startswith("create index") or 
            proposed_clean.startswith("create unique index") or 
            proposed_clean.startswith("analyze")
        )
        if not allowed_prefix:
            return {
                "approved": False,
                "reason": "The proposed SQL command is not an authorized schema modification (must be CREATE INDEX or ANALYZE).",
                "violation_detected": True,
                "violation_details": f"Unauthorized command starting pattern: {proposed_sql[:20]}..."
            }

        # Safe and Approved!
        return {
            "approved": True,
            "reason": "Proposed SQL is verified as a safe, non-blocking index creation statement.",
            "violation_detected": False,
            "violation_details": None
        }

    def _check_query_safety(self, sql: str, is_proposal: bool) -> Tuple[bool, str]:
        """
        Helper to scan SQL text for blacklisted keywords, stacked queries, and SQL injections.
        """
        sql_clean = sql.strip().lower()

        # Check for stacked queries (multiple queries separated by semicolons)
        # Allow trailing semicolon, but reject semicolons in the middle of statements
        semicolon_count = sql_clean.count(";")
        if semicolon_count > 1 or (semicolon_count == 1 and not sql_clean.endswith(";")):
            return False, "Stacked queries separated by semicolons are strictly prohibited to prevent SQL injection."

        # Scan for blacklisted keywords using regex
        for pattern in self.blacklist_keywords:
            if re.search(pattern, sql_clean):
                matched_keyword = pattern.replace(r"\b", "")
                return False, f"Prohibited SQL keyword detected: '{matched_keyword.upper()}'."

        # Check for unsafe ALTER TABLE clauses
        if "alter table" in sql_clean:
            if "drop" in sql_clean or "rename" in sql_clean:
                return False, "Unsafe ALTER TABLE operation detected (dropping columns or renaming tables is forbidden)."

        return True, ""
