import re


class SQLGuard:
    FORBIDDEN = ["DELETE", "UPDATE", "INSERT", "DROP", "ALTER", "TRUNCATE"]
    IDENTIFIER_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")

    def check(self, sql: str, allowed_identifiers: set[str] | None = None) -> tuple[bool, str | None]:
        upper_sql = sql.upper()

        for keyword in self.FORBIDDEN:
            if keyword in upper_sql:
                return False, f"forbidden keyword detected: {keyword}"

        if "SELECT" not in upper_sql:
            return False, "only SELECT queries are allowed"

        if ";" in sql:
            return False, "semicolon is not allowed"

        if allowed_identifiers:
            for identifier in allowed_identifiers:
                if not self.IDENTIFIER_PATTERN.fullmatch(identifier):
                    return False, f"invalid identifier detected: {identifier}"

        return True, None
