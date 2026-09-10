"""
app.py
Flask web server for the AI Database Explorer.

Serves the frontend (templates/index.html + static/) and exposes:
  GET  /api/schema  -> table + column info, for the sidebar
  POST /api/chat     -> {"message": "..."} -> structured bot reply

Run with:
    python app.py
Then open http://127.0.0.1:5000 in your browser.
"""

from flask import Flask, jsonify, request, render_template

from db_setup import build_database, DB_NAME
from chatbot import Chatbot
from query_builder import QueryError

app = Flask(__name__)

build_database(DB_NAME, overwrite=False)
bot = Chatbot(DB_NAME)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/schema")
def schema():
    """Return table names + their columns, for the sidebar schema browser."""
    try:
        tables = bot.qb.list_tables()
        result = []
        for table in tables:
            columns = bot.qb.describe_table(table)
            result.append({
                "name": table,
                "columns": [{"name": c, "type": t} for c, t in columns],
            })
        return jsonify({"tables": result})
    except QueryError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"type": "error", "message": "Please type a question."}), 400

    result = bot.respond_structured(message)
    return jsonify(result)


if __name__ == "__main__":
    print("\nAI Database Explorer running at http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)
