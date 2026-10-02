/* Site assistant — messenger-style widget (Home / Messages / Help).

   Two conversation modes share the panel:
     ask      — Ask Caraïbes, grounded Q&A over the knowledge base
     project  — Project Assistant, builds an event brief and submits it

   Each mode keeps its own transcript in sessionStorage so they survive page
   changes within a visit; the server (POST /chat) is stateless and receives
   the recent turns with every message. Replies are rendered as text only.

   Nothing is submitted to Let's Connect until the visitor clicks the confirm
   button the server asks for (ready: true) — that click is the only thing that
   ever sends confirm: true. */
(() => {
  const root = document.getElementById("chat");
  if (!root) return;

  const $ = (id) => document.getElementById(id);
  const launcher = $("chat-launcher");
  const panel = $("chat-panel");
  const log = $("chat-log");
  const form = $("chat-form");
  const input = $("chat-input");
  const send = $("chat-send");
  const chips = $("chat-chips");
  const reset = $("chat-reset");
  const badge = $("chat-badge");
  const endpoint = root.dataset.endpoint;
  const panes = [...panel.querySelectorAll("[data-view-pane]")];
  const tabs = [...panel.querySelectorAll(".chat__tabs [data-go]")];
  const modeButtons = [...panel.querySelectorAll("[data-mode]")];
  const STORE = "ci-chat";
  const VIEW_STORE = "ci-chat-view";
  const MODE_STORE = "ci-chat-mode";

  const MODES = {
    ask: {
      greeting:
        "Hello! I'm the Caribbean Incentive assistant. Ask me about our islands, services, getting there — or give me a group size and nights for a quick planning estimate.",
      placeholder: "Write a message…",
      note: "Estimates are indicative and exclude airfare.",
    },
    project: {
      greeting:
        "Let's shape your project. Tell me what kind of event you have in mind, roughly how many people and when — I'll ask for the rest, then you can send the brief to our team.",
      placeholder: "Describe your project…",
      note: "Nothing is sent until you confirm the summary.",
    },
  };

  const noteEl = panel.querySelector(".chat__note");
  let histories = { ask: [], project: [] };
  let mode = "ask";
  let busy = false;
  let view = "home";
  let unread = 0;

  const history = () => histories[mode];

  const read = (key, fallback) => {
    try { return JSON.parse(sessionStorage.getItem(key)) ?? fallback; } catch (_) { return fallback; }
  };
  const write = (key, value) => {
    try { sessionStorage.setItem(key, JSON.stringify(value)); } catch (_) {}
  };
  const save = () => write(STORE, { ask: histories.ask.slice(-20), project: histories.project.slice(-20) });

  /* ------------------------------------------------------------ views */
  const show = (name, { focus = true } = {}) => {
    view = name;
    panel.dataset.view = name;
    panes.forEach((p) => { p.hidden = p.dataset.viewPane !== name; });
    tabs.forEach((t) => {
      if (t.dataset.go === name) t.setAttribute("aria-current", "page");
      else t.removeAttribute("aria-current");
    });
    write(VIEW_STORE, name);
    if (name === "messages") {
      unread = 0;
      syncBadge();
      log.scrollTop = log.scrollHeight;
      if (focus) window.setTimeout(() => input.focus({ preventScroll: true }), 60);
    }
  };

  const syncBadge = () => {
    badge.hidden = unread === 0;
    badge.textContent = unread ? String(unread) : "";
  };

  const setMode = (next, { rerender = true } = {}) => {
    if (!MODES[next] || busy) return;
    mode = next;
    write(MODE_STORE, mode);
    modeButtons.forEach((b) => {
      const on = b.dataset.mode === mode;
      b.classList.toggle("is-active", on);
      b.setAttribute("aria-selected", String(on));
    });
    input.placeholder = MODES[mode].placeholder;
    if (noteEl) noteEl.textContent = MODES[mode].note;
    if (rerender) render();
  };

  /* --------------------------------------------------------- messages */
  const bubble = (role, text) => {
    const row = document.createElement("div");
    row.className = `chat__row chat__row--${role}`;
    if (role === "bot") {
      const av = document.createElement("span");
      av.className = "chat__avatar chat__avatar--sm";
      av.setAttribute("aria-hidden", "true");
      av.textContent = "CI";
      row.appendChild(av);
    }
    const el = document.createElement("div");
    el.className = `chat__msg chat__msg--${role}`;
    el.textContent = text; // text only — replies are never parsed as HTML
    row.appendChild(el);
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
    return row;
  };

  const typing = () => {
    const row = bubble("bot", "");
    const el = row.querySelector(".chat__msg");
    el.classList.add("chat__typing");
    el.setAttribute("aria-label", "Assistant is typing");
    el.innerHTML = "<span></span><span></span><span></span>";
    return row;
  };

  /* The only path that sends confirm: true. */
  const confirmCard = () => {
    const wrap = document.createElement("div");
    wrap.className = "chat__confirm";

    const yes = document.createElement("button");
    yes.type = "button";
    yes.className = "chat__confirm-btn chat__confirm-btn--gold";
    yes.textContent = "Submit my brief";

    const no = document.createElement("button");
    no.type = "button";
    no.className = "chat__confirm-btn";
    no.textContent = "Not yet — let me change something";

    yes.addEventListener("click", () => { wrap.remove(); submit(); });
    no.addEventListener("click", () => {
      wrap.remove();
      input.focus({ preventScroll: true });
    });

    wrap.append(yes, no);
    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
  };

  const render = () => {
    log.innerHTML = "";
    bubble("bot", MODES[mode].greeting);
    history().forEach((m) => bubble(m.role === "user" ? "user" : "bot", m.content));
    chips.hidden = mode !== "ask" || history().length > 0;
  };

  const autosize = () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
  };

  const post = async (body) => {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.json();
  };

  const finish = (data, fallback) => {
    const text = (data && data.reply) || fallback;
    history().push({ role: "assistant", content: text });
    save();
    bubble("bot", text);
    if (data && data.ready) confirmCard();
    busy = false;
    send.disabled = false;
    if (view !== "messages" || panel.hidden) { unread += 1; syncBadge(); }
    else input.focus({ preventScroll: true });
  };

  const ask = async (text) => {
    const message = (text || "").trim();
    if (!message || busy) return;
    show("messages", { focus: false });
    busy = true;
    send.disabled = true;
    chips.hidden = true;

    history().push({ role: "user", content: message });
    save();
    bubble("user", message);
    input.value = "";
    autosize();
    const dots = typing();

    let data = null;
    try {
      data = await post({ messages: history(), mode });
    } catch (_) {
      /* keep the fallback reply */
    }
    dots.remove();
    finish(data, "Sorry — I couldn't reach the assistant just now. You can always reach the team through Let's Connect.");
  };

  const submit = async () => {
    if (busy) return;
    busy = true;
    send.disabled = true;
    const dots = typing();
    let data = null;
    try {
      data = await post({ messages: history(), mode: "project", confirm: true });
    } catch (_) {
      /* keep the fallback reply */
    }
    dots.remove();
    finish(data, "I couldn't send your brief just now — please try again, or use the Let's Connect page.");
  };

  /* ----------------------------------------------------- open / close */
  const setOpen = (open) => {
    panel.hidden = !open;
    root.classList.toggle("is-open", open);
    launcher.setAttribute("aria-expanded", String(open));
    launcher.setAttribute("aria-label", open ? "Close the assistant" : "Open the Caribbean Incentive assistant");
    if (open) show(view);
  };

  launcher.addEventListener("click", () => setOpen(panel.hidden));
  panel.addEventListener("click", (e) => {
    const start = e.target.closest("[data-mode-start]");
    if (start) { setMode(start.dataset.modeStart); return show("messages"); }
    const pick = e.target.closest("[data-mode]");
    if (pick) return setMode(pick.dataset.mode);
    const go = e.target.closest("[data-go]");
    if (go) return show(go.dataset.go);
    const topic = e.target.closest("[data-ask]");
    if (topic) { setMode("ask", { rerender: false }); return ask(topic.dataset.ask); }
    if (e.target.closest("[data-chat-close]")) { setOpen(false); launcher.focus(); }
  });
  panel.querySelector("[data-chat-search]").addEventListener("submit", (e) => {
    e.preventDefault();
    const field = e.currentTarget.querySelector("input");
    setMode("ask", { rerender: false });
    ask(field.value);
    field.value = "";
  });
  form.addEventListener("submit", (e) => { e.preventDefault(); ask(input.value); });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(input.value); }
  });
  input.addEventListener("input", autosize);
  chips.addEventListener("click", (e) => {
    const chip = e.target.closest(".chat__chip");
    if (chip) ask(chip.textContent);
  });
  reset.addEventListener("click", () => {
    histories[mode] = [];
    save();
    render();
    input.focus({ preventScroll: true });
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !panel.hidden) { setOpen(false); launcher.focus(); }
  });

  const stored = read(STORE, null);
  if (Array.isArray(stored)) histories.ask = stored;          // transcript from the previous version
  else if (stored && typeof stored === "object") histories = { ask: stored.ask || [], project: stored.project || [] };
  view = read(VIEW_STORE, "home");
  if (!["home", "messages", "help"].includes(view)) view = "home";
  setMode(read(MODE_STORE, "ask") === "project" ? "project" : "ask", { rerender: false });
  render();
})();
