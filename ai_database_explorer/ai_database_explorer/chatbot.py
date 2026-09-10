"""
chatbot.py
The conversational layer of the AI Database Explorer.

Takes user input -> parses intent with nlu_engine -> runs the right
query via query_builder -> returns a structured result.

`respond()` returns a plain string (used by the CLI in main.py).
`respond_structured()` returns a dict with columns/rows kept separate
(used by the Flask web frontend, so it can render real HTML tables).
"""

from nlu_engine import parse
from query_builder import QueryBuilder, QueryError

HELP_TEXT = """Here's what you can ask me (I understand plain English, not just SQL!):

  • "show all employees"              -> list every row in a table
  • "list products"
  • "what tables are there?"          -> show database schema
  • "describe employees"              -> show a table's columns
  • "how many employees are there"    -> count rows
  • "how many employees in Sales"     -> count rows matching a value
  • "find employees named Alice"      -> search by name
  • "show products under 50"          -> numeric filter (< / <=)
  • "employees over 90000"            -> numeric filter (> / >=)
  • "departments in Chicago"          -> search by location

Type 'exit' or 'quit' whenever you're done."""

WELCOME_TEXT = """
========================================
   🤖  AI Database Explorer (Python)
========================================
Ask me questions about the sample company
database in plain English. Type 'help'
to see examples, or 'exit' to quit.
"""


def format_table(columns, rows) -> str:
    """Render columns/rows as a plain-text table (used by the CLI)."""
    if not rows:
        return "No matching records found."

    widths = [len(c) for c in columns]
    str_rows = []
    for row in rows:
        str_row = [str(v) for v in row]
        str_rows.append(str_row)
        for i, v in enumerate(str_row):
            widths[i] = max(widths[i], len(v))

    def format_row(values):
        return " | ".join(v.ljust(widths[i]) for i, v in enumerate(values))

    lines = [format_row(columns)]
    lines.append("-+-".join("-" * w for w in widths))
    for str_row in str_rows:
        lines.append(format_row(str_row))
    lines.append(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")
    return "\n".join(lines)


class Chatbot:
    def __init__(self, db_path: str):
        self.qb = QueryBuilder(db_path)

    def _handle(self, user_text: str) -> dict:
        """
        Core logic shared by both the CLI and the web API.
        Returns a structured dict:
            {
              "type": "text" | "table" | "exit" | "error",
              "message": str (present for text/exit/error),
              "columns": list[str] (present for table),
              "rows": list[list] (present for table),
            }
        """
        parsed = parse(user_text)
        intent = parsed.get("intent")

        try:
            if intent == "greeting":
                return {
                    "type": "text",
                    "message": "Hello! Ask me about employees, departments, or "
                    "products. Type 'help' for examples.",
                }

            if intent == "help":
                return {"type": "text", "message": HELP_TEXT}

            if intent == "exit":
                return {"type": "exit", "message": "Goodbye! 👋"}

            if intent == "schema":
                tables = self.qb.list_tables()
                message = "The database has these tables:\n  - " + "\n  - ".join(tables)
                return {"type": "text", "message": message}

            if intent == "describe":
                table = parsed.get("table")
                if not table:
                    return {
                        "type": "text",
                        "message": "Which table did you mean? Try: employees, "
                        "departments, or products.",
                    }
                cols = self.qb.describe_table(table)
                lines = [f"Columns in '{table}':"]
                for name, dtype in cols:
                    lines.append(f"  - {name} ({dtype})")
                return {"type": "text", "message": "\n".join(lines)}

            if intent == "count":
                table = parsed.get("table")
                if not table:
                    return {
                        "type": "text",
                        "message": "Which table would you like me to count? "
                        "(employees, departments, products)",
                    }
                total = self.qb.count(table, parsed.get("column"), parsed.get("value"))
                if parsed.get("value"):
                    message = f"There are {total} record(s) in '{table}' matching '{parsed['value']}'."
                else:
                    message = f"There are {total} record(s) in '{table}'."
                return {"type": "text", "message": message}

            if intent == "show_all":
                table = parsed.get("table")
                if not table:
                    return {
                        "type": "text",
                        "message": "Which table would you like to see? "
                        "(employees, departments, products)",
                    }
                columns, rows = self.qb.show_all(table)
                return {"type": "table", "columns": columns, "rows": rows}

            if intent == "filter":
                table = parsed.get("table")
                if not table:
                    return {
                        "type": "text",
                        "message": "Which table should I filter? "
                        "(employees, departments, products)",
                    }
                columns, rows = self.qb.filter_rows(
                    table,
                    parsed.get("column"),
                    parsed.get("operator", "LIKE"),
                    parsed.get("value"),
                )
                return {"type": "table", "columns": columns, "rows": rows}

            return {
                "type": "text",
                "message": "I'm not sure I understood that. Try things like "
                "\"show all employees\" or type 'help' for examples.",
            }

        except QueryError as e:
            return {"type": "error", "message": f"Sorry, I hit a problem: {e}"}
        except Exception as e:  # keep the chatbot from crashing on unexpected input
            return {"type": "error", "message": f"Something went wrong while processing that: {e}"}

    def respond_structured(self, user_text: str) -> dict:
        """Structured result for the web frontend."""
        return self._handle(user_text)

    def respond(self, user_text: str) -> str:
        """Plain-string result for the CLI (main.py)."""
        result = self._handle(user_text)

        if result["type"] == "exit":
            return "__EXIT__"
        if result["type"] == "table":
            return format_table(result["columns"], result["rows"])
        return result["message"]
