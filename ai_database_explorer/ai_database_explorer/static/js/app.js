// app.js — talks to the Flask API and renders the console-style UI

const transcript = document.getElementById("transcript");
const composer = document.getElementById("composer");
const input = document.getElementById("message-input");
const schemaTree = document.getElementById("schema-tree");

function scrollToBottom() {
  transcript.scrollTop = transcript.scrollHeight;
}

function addYouEntry(text) {
  const entry = document.createElement("div");
  entry.className = "entry entry-you";
  entry.innerHTML = `
    <div class="entry-label">you</div>
    <div class="entry-body"></div>
  `;
  entry.querySelector(".entry-body").textContent = text;
  transcript.appendChild(entry);
  scrollToBottom();
}

function isNumeric(value) {
  return typeof value === "number";
}

function buildResultTable(columns, rows) {
  const wrap = document.createElement("div");
  wrap.className = "result-table-wrap";

  const meta = document.createElement("div");
  meta.className = "result-meta";
  meta.textContent = `${rows.length} row${rows.length !== 1 ? "s" : ""}`;
  wrap.appendChild(meta);

  if (rows.length === 0) {
    const empty = document.createElement("div");
    empty.style.padding = "14px 16px";
    empty.style.color = "var(--text-muted)";
    empty.style.fontFamily = "var(--font-mono)";
    empty.style.fontSize = "13px";
    empty.textContent = "No matching records found.";
    wrap.appendChild(empty);
    return wrap;
  }

  const table = document.createElement("table");
  table.className = "result-table";

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value;
      if (isNumeric(value)) td.classList.add("numeric");
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  wrap.appendChild(table);
  return wrap;
}

function addBotEntry(result) {
  const entry = document.createElement("div");
  entry.className = "entry entry-bot";
  if (result.type === "error") entry.classList.add("is-error");

  const label = document.createElement("div");
  label.className = "entry-label";
  label.textContent = "bot";
  entry.appendChild(label);

  if (result.type === "table") {
    entry.appendChild(buildResultTable(result.columns, result.rows));
  } else {
    const body = document.createElement("div");
    body.className = "entry-body";
    body.textContent = result.message;
    entry.appendChild(body);
  }

  transcript.appendChild(entry);
  scrollToBottom();
}

async function sendMessage(text) {
  addYouEntry(text);

  const button = composer.querySelector("button");
  button.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const result = await res.json();
    addBotEntry(result);
  } catch (err) {
    addBotEntry({ type: "error", message: "Couldn't reach the server. Is app.py still running?" });
  } finally {
    button.disabled = false;
    input.focus();
  }
}

composer.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendMessage(text);
});

// ---------- schema sidebar ----------

async function loadSchema() {
  try {
    const res = await fetch("/api/schema");
    const data = await res.json();

    schemaTree.innerHTML = "";

    data.tables.forEach((table) => {
      const wrap = document.createElement("div");
      wrap.className = "schema-table";

      const button = document.createElement("button");
      button.className = "schema-table-name";
      button.innerHTML = `<span class="dot"></span>${table.name}`;
      button.addEventListener("click", () => {
        wrap.classList.toggle("open");
      });

      const columnsWrap = document.createElement("div");
      columnsWrap.className = "schema-columns";
      table.columns.forEach((col) => {
        const line = document.createElement("div");
        line.className = "schema-column";
        line.innerHTML = `${col.name} <span class="col-type">${col.type}</span>`;
        columnsWrap.appendChild(line);
      });

      const askLine = document.createElement("div");
      askLine.className = "schema-column schema-action";
      askLine.textContent = `show all ${table.name}`;
      askLine.addEventListener("click", (ev) => {
        ev.stopPropagation();
        sendMessage(`show all ${table.name}`);
      });
      columnsWrap.appendChild(askLine);

      wrap.appendChild(button);
      wrap.appendChild(columnsWrap);
      schemaTree.appendChild(wrap);
    });
  } catch (err) {
    schemaTree.innerHTML = '<div class="schema-loading">Couldn\'t load schema.</div>';
  }
}

loadSchema();
input.focus();
