"""
nlu_engine.py
A lightweight, rule-based "Natural Language Understanding" engine.

It doesn't call any external AI API — instead it uses regex patterns,
keyword matching, and fuzzy string matching (difflib) to turn plain
English questions into a structured intent the chatbot can act on.

This keeps the project dependency-free and fully offline, while still
behaving like a smart natural-language interface to the database.
"""

import re
import difflib

TABLES = {
    "employees": ["employee", "employees", "staff", "worker", "workers"],
    "departments": ["department", "departments", "dept", "depts"],
    "products": ["product", "products", "item", "items", "inventory"],
}

# Map friendly synonyms -> real column names, per table
COLUMN_ALIASES = {
    "employees": {
        "name": ["name", "named", "called"],
        "department": ["department", "dept", "team"],
        "salary": ["salary", "pay", "wage", "income"],
        "hire_date": ["hire_date", "hired", "joined", "start date"],
        "email": ["email", "mail"],
    },
    "products": {
        "name": ["name", "named", "called"],
        "category": ["category", "type", "kind"],
        "price": ["price", "cost", "priced"],
        "stock": ["stock", "quantity", "inventory", "available"],
    },
    "departments": {
        "name": ["name", "named", "called"],
        "location": ["location", "city", "based", "located"],
    },
}

GREETINGS = {"hi", "hello", "hey", "yo", "greetings"}
HELP_WORDS = {"help", "commands", "options", "what can you do"}
EXIT_WORDS = {"exit", "quit", "bye", "goodbye", "stop"}
SCHEMA_WORDS = {"tables", "schema", "database", "structure"}

# When a table/column isn't explicitly named, fall back to the most
# sensible column for that kind of question.
DEFAULT_LOCATION_COLUMN = {
    "departments": "location",
    "employees": "department",
    "products": "category",
}

DEFAULT_NUMERIC_COLUMN = {
    "employees": "salary",
    "products": "price",
    "departments": None,
}


def _find_table(text: str):
    """Fuzzy-match any mention of a table name in the text."""
    words = re.findall(r"[a-zA-Z]+", text.lower())
    for canonical, synonyms in TABLES.items():
        for w in words:
            match = difflib.get_close_matches(w, synonyms, n=1, cutoff=0.8)
            if match:
                return canonical
    return None


def _find_column(table: str, text: str):
    if table not in COLUMN_ALIASES:
        return None
    words = re.findall(r"[a-zA-Z]+", text.lower())
    for column, synonyms in COLUMN_ALIASES[table].items():
        for w in words:
            if difflib.get_close_matches(w, synonyms, n=1, cutoff=0.8):
                return column
    return None


def _extract_number(text: str):
    match = re.search(r"(\d+(\.\d+)?)", text)
    return float(match.group(1)) if match else None


def _extract_quoted_or_named_value(text: str):
    """
    Pulls a value out of phrases like:
      'named John', 'called Sales', 'with email x@y.com', 'in Chicago'
    """
    patterns = [
        r"(?:named|called|name is)\s+([a-zA-Z ]+)",
        r"(?:in|from|at)\s+([a-zA-Z ]+)",
        r"(?:is|=)\s+([a-zA-Z0-9. ]+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def parse(text: str) -> dict:
    """
    Parse free-form user text into a structured intent dictionary:
        {
          "intent": "greeting" | "help" | "exit" | "schema" |
                     "describe" | "count" | "show_all" | "filter" | "unknown",
          "table": str or None,
          "column": str or None,
          "operator": str or None,   # '>', '<', '='
          "value": str/float or None,
        }
    """
    raw = text.strip()
    lower = raw.lower()

    if lower in GREETINGS or any(lower.startswith(g) for g in GREETINGS):
        return {"intent": "greeting"}

    if any(h in lower for h in HELP_WORDS):
        return {"intent": "help"}

    if any(e == lower or lower.startswith(e) for e in EXIT_WORDS):
        return {"intent": "exit"}

    if any(s in lower for s in SCHEMA_WORDS) and "describe" not in lower:
        return {"intent": "schema"}

    table = _find_table(lower)

    if "describe" in lower or "columns" in lower or "structure of" in lower:
        return {"intent": "describe", "table": table}

    if "how many" in lower or lower.startswith("count"):
        value = _extract_quoted_or_named_value(lower)
        column = _find_column(table, lower) if table else None
        if not column and value and table:
            column = DEFAULT_LOCATION_COLUMN.get(table)
        return {
            "intent": "count",
            "table": table,
            "column": column,
            "operator": "=",
            "value": value,
        }

    # Comparison filters e.g. "under 50", "over 70000", "above 100"
    comp_match = re.search(r"(under|below|less than|cheaper than)\s+(\d+(\.\d+)?)", lower)
    if comp_match:
        column = _find_column(table, lower) if table else None
        if not column and table:
            column = DEFAULT_NUMERIC_COLUMN.get(table)
        return {
            "intent": "filter",
            "table": table,
            "column": column,
            "operator": "<",
            "value": float(comp_match.group(2)),
        }

    comp_match = re.search(r"(over|above|more than|greater than)\s+(\d+(\.\d+)?)", lower)
    if comp_match:
        column = _find_column(table, lower) if table else None
        if not column and table:
            column = DEFAULT_NUMERIC_COLUMN.get(table)
        return {
            "intent": "filter",
            "table": table,
            "column": column,
            "operator": ">",
            "value": float(comp_match.group(2)),
        }

    if "named" in lower or "called" in lower:
        value = _extract_quoted_or_named_value(lower)
        if value and table:
            column = _find_column(table, lower) or "name"
            return {
                "intent": "filter",
                "table": table,
                "column": column,
                "operator": "LIKE",
                "value": value,
            }

    if " in " in lower or " from " in lower or " at " in lower:
        value = _extract_quoted_or_named_value(lower)
        if value and table:
            column = _find_column(table, lower) or DEFAULT_LOCATION_COLUMN.get(table, "name")
            return {
                "intent": "filter",
                "table": table,
                "column": column,
                "operator": "LIKE",
                "value": value,
            }

    if any(k in lower for k in ["show", "list", "display", "all", "get"]) and table:
        return {"intent": "show_all", "table": table}

    if table:
        # Table mentioned but nothing else recognized -> default to show_all
        return {"intent": "show_all", "table": table}

    return {"intent": "unknown"}
