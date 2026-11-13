/* nass · plurals — a small authoring page for the plural lexicon.
   Everything lives in localStorage; Export writes a JSON file that
   tools/merge_overrides.py turns into src/nass/data/overrides.jsonl. */

const KEY = "nass-plurals-v1";
const DATA = window.NASS_DATA || { gaps: [], verify: [] };

let state = load();
let mode = "gaps";
let queue = [];
let index = 0;

const $ = (id) => document.getElementById(id);

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) || "{}");
    return { gaps: raw.gaps || {}, verify: raw.verify || {} };
  } catch {
    return { gaps: {}, verify: {} };
  }
}

function save() {
  localStorage.setItem(KEY, JSON.stringify(state));
}

function buildQueue() {
  const source = mode === "gaps" ? DATA.gaps : DATA.verify;
  const done = state[mode];
  queue = source.filter((item) => !(item.w in done));
  index = 0;
}

function counts() {
  $("n-gaps").textContent = DATA.gaps.length - Object.keys(state.gaps).length;
  $("n-verify").textContent = DATA.verify.length - Object.keys(state.verify).length;
}

function render() {
  counts();
  const card = $("card");
  const done = $("done");

  if (index >= queue.length) {
    card.hidden = true;
    done.hidden = false;
    $("progress").textContent = `${mode === "gaps" ? "gaps" : "verify"} · complete`;
    return;
  }

  card.hidden = false;
  done.hidden = true;

  const item = queue[index];
  $("meta").textContent = `#${item.rank} · ${mode === "gaps" ? "no plural recorded" : "recorded"}`;
  $("word").textContent = item.w;
  $("gloss").textContent = item.g || "";

  if (mode === "verify") {
    const pl = (item.pl || []).join("، ");
    const du = (item.du || []).join("، ");
    $("current").textContent = `current: ${pl || "—"}${du ? ` · dual ${du}` : ""}`;
    $("pl").value = pl;
    $("du").value = du;
    $("pl").classList.remove("suggested");
    $("hint").textContent = "";
    $("save").innerHTML = "Confirm <kbd>↵</kbd>";
  } else {
    const suggestion = item.s || "";
    $("current").textContent = "";
    $("pl").value = suggestion;
    $("du").value = "";
    $("pl").classList.toggle("suggested", Boolean(suggestion));
    $("hint").textContent = suggestion
      ? item.st === "source"
        ? "suggested from Wiktionary — confirm or edit"
        : "suggested by rule — confirm or edit"
      : "";
    $("save").innerHTML = suggestion ? "Confirm <kbd>↵</kbd>" : "Save <kbd>↵</kbd>";
  }

  $("progress").textContent = `${index + 1} / ${queue.length}`;
  $("pl").focus();
}

function record(entry) {
  const item = queue[index];
  state[mode][item.w] = { ...entry, at: new Date().toISOString() };
  save();
  index += 1;
  render();
}

function split(value) {
  return value
    .split(/[،,\n]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

$("save").addEventListener("click", () => {
  const pl = split($("pl").value);
  const du = split($("du").value);
  if (!pl.length && !du.length) {
    $("pl").focus();
    return;
  }
  record({ pl, du, none: false });
});

$("none").addEventListener("click", () => record({ pl: [], du: [], none: true }));
$("pl").addEventListener("input", () => $("pl").classList.remove("suggested"));
$("skip").addEventListener("click", () => {
  index += 1;
  render();
});

document.querySelectorAll("nav button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach((b) => b.classList.remove("active"));
    button.classList.add("active");
    mode = button.dataset.mode;
    buildQueue();
    render();
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && event.target.tagName !== "BUTTON") {
    event.preventDefault();
    $("save").click();
  }
  if (event.key === "Escape") {
    event.preventDefault();
    $("skip").click();
  }
});

function exportJSON() {
  const payload = {
    generated: new Date().toISOString(),
    gaps: state.gaps,
    verify: state.verify,
  };
  const blob = new Blob([JSON.stringify(payload, null, 1)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "nass-overrides.json";
  link.click();
  URL.revokeObjectURL(url);
}

$("export").addEventListener("click", exportJSON);
$("export2").addEventListener("click", exportJSON);

$("reset").addEventListener("click", () => {
  if (!confirm("Clear every entry you have made on this device?")) return;
  state = { gaps: {}, verify: {} };
  save();
  buildQueue();
  render();
});

buildQueue();
render();
