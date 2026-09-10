# AI Database Explorer 🤖🗄️

A Python chatbot that lets you explore a SQLite database using plain
English — no SQL knowledge required. Comes with both a **command-line
version** and a **local web app** (Flask backend + browser frontend).

It's fully offline: instead of calling an external AI API, it uses a
rule-based Natural Language Understanding (NLU) engine (regex +
fuzzy matching) to turn your questions into safe, parameterized SQL
queries.

## Project structure

```
ai_database_explorer/
├── main.py             # CLI entry point
├── app.py              # Flask web server entry point
├── chatbot.py          # conversational layer, shared by CLI + web
├── nlu_engine.py        # parses plain English into structured intents
├── query_builder.py     # turns intents into safe SQL, executes them
├── db_setup.py          # creates + seeds the sample SQLite database
├── requirements.txt      # Flask, for the web version
├── templates/
│   └── index.html       # web frontend markup
├── static/
│   ├── css/
│   │   └── style.css     # web frontend styling
│   └── js/
│       └── app.js        # web frontend behavior
└── README.md
```

`company.db` is created automatically the first time you run either
`main.py` or `app.py` — you don't need to create it yourself.

## Sample database

- **departments** (id, name, location)
- **employees** (id, name, department, salary, hire_date, email)
- **products** (id, name, category, price, stock)

## Option A — command line

Requires Python 3.7+, standard library only, no installs needed.

```bash
python main.py
```

## Option B — local web app

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser. You'll see:
- a **schema sidebar** on the left — click a table to expand its
  columns, click "show all `<table>`" to run a quick query
- a **chat transcript** in the middle — your questions and the bot's
  answers, with query results rendered as real, styled tables
- an **input bar** at the bottom to type your own questions

Press `Ctrl+C` in the terminal to stop the server.

## Example conversation (works in both versions)

```
You: what tables are there?
Bot: The database has these tables:
  - departments
  - employees
  - products

You: show all employees
Bot: id | name          | department  | salary  | hire_date  | email
     ...

You: how many employees in Sales
Bot: There are 2 record(s) in 'employees' matching 'sales'.

You: find employees named Alice
Bot: id | name          | department | salary | hire_date | email
     1  | Alice Johnson | Sales      | 62000  | ...

You: products under 20
Bot: id | name           | category    | price | stock
     ...

You: exit
Bot: Goodbye! 👋
```

## Things you can ask

- `show all employees` / `list products` / `display departments`
- `what tables are there?` / `schema`
- `describe employees` (see column names/types)
- `how many products are there`
- `how many employees in Sales`
- `find employees named Alice` / `department called Finance`
- `products under 50` / `employees over 90000`
- `departments in Chicago`

## How it works (the "AI" part)

1. **`nlu_engine.py`** scans your sentence for:
   - table names (with fuzzy matching, so small typos still work)
   - column names (via synonym lists, e.g. "pay"/"wage" → `salary`)
   - comparison words ("under", "over", "more than", etc.)
   - filter values ("named X", "in X", "called X")
   and returns a structured intent dictionary.

2. **`query_builder.py`** turns that intent into a parameterized SQL
   query (never string-concatenated values, so it's injection-safe)
   and runs it against `company.db`.

3. **`chatbot.py`** has one shared brain (`_handle()`) used by both
   interfaces:
   - `respond()` returns a plain string, for the CLI.
   - `respond_structured()` returns a dict with `columns`/`rows` kept
     separate, so the web frontend (`app.js`) can build a real HTML
     `<table>` instead of a preformatted text block.

4. **`app.py`** is a small Flask server with two endpoints:
   - `GET /api/schema` — table/column info for the sidebar
   - `POST /api/chat` — takes `{"message": "..."}`, returns the
     structured bot reply as JSON

## Troubleshooting

- **Page loads but has no styling / colors** — usually means
  `static/css/style.css` isn't at the right path. It MUST be at
  `static/css/style.css`, and the `static/` folder MUST sit directly
  next to `app.py` (not inside another folder). Restart the server
  after fixing, then hard-refresh your browser (Ctrl+Shift+R).
- **`ModuleNotFoundError: No module named 'flask'`** — run
  `pip install -r requirements.txt` (or `pip install flask`) first.
- **`AttributeError: 'Chatbot' object has no attribute
  'respond_structured'`** — you're using an old copy of `chatbot.py`
  that only has `respond()`. Use the version included in this
  project — it has both `respond()` and `respond_structured()`.

## Extending it

- Add new tables in `db_setup.py` and register their columns in
  `SCHEMA_COLUMNS` (in `query_builder.py`) and `TABLES` (in
  `nlu_engine.py`).
- Add more phrasing synonyms to `COLUMN_ALIASES` in `nlu_engine.py`.
- Swap in a real LLM: replace `nlu_engine.parse()` with a call to an
  AI API that returns the same structured intent dictionary — the
  rest of the app (`query_builder.py`, `chatbot.py`, `app.py`)
  doesn't need to change at all.
