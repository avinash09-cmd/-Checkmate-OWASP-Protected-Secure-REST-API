// Checkmate frontend — talks to the FastAPI backend at the same origin.
// NOTE on the token: this demo keeps the JWT in localStorage for simplicity.
// A production app would prefer a short-lived token held in memory plus an
// HttpOnly refresh cookie, since localStorage is readable by any script that
// runs on the page (i.e. vulnerable if an XSS bug ever slipped through).

const TOKEN_KEY = "checkmate_token";
const EMAIL_KEY = "checkmate_email";

const el = (id) => document.getElementById(id);

// ---------- views ----------
const authView = el("auth-view");
const dashboardView = el("dashboard-view");

function showAuthView() {
  authView.hidden = false;
  dashboardView.hidden = true;
}

function showDashboardView() {
  authView.hidden = true;
  dashboardView.hidden = false;
}

// ---------- API helper ----------
async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = localStorage.getItem(TOKEN_KEY);
  if (auth && token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    // Token missing/expired/invalid — send the user back to login.
    logout();
    throw new Error("Session expired. Please log in again.");
  }

  let data = null;
  try {
    data = await res.json();
  } catch {
    /* no JSON body, e.g. 204 No Content */
  }

  if (!res.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg).join(", ")
      : detail || "Something went wrong.";
    throw new Error(message);
  }

  return data;
}

// ---------- auth tabs ----------
const tabLogin = el("tab-login");
const tabRegister = el("tab-register");
const loginForm = el("login-form");
const registerForm = el("register-form");

tabLogin.addEventListener("click", () => switchTab("login"));
tabRegister.addEventListener("click", () => switchTab("register"));

function switchTab(which) {
  const toLogin = which === "login";
  tabLogin.classList.toggle("is-active", toLogin);
  tabRegister.classList.toggle("is-active", !toLogin);
  tabLogin.setAttribute("aria-selected", String(toLogin));
  tabRegister.setAttribute("aria-selected", String(!toLogin));
  loginForm.hidden = !toLogin;
  registerForm.hidden = toLogin;
}

// ---------- login ----------
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = el("login-message");
  msg.textContent = "";
  msg.className = "form-message";

  const email = el("login-email").value.trim();
  const password = el("login-password").value;

  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(EMAIL_KEY, email);
    loginForm.reset();
    await enterDashboard();
  } catch (err) {
    msg.textContent = err.message;
    msg.className = "form-message is-error";
  }
});

// ---------- register ----------
registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = el("register-message");
  msg.textContent = "";
  msg.className = "form-message";

  const email = el("register-email").value.trim();
  const password = el("register-password").value;

  try {
    await api("/auth/register", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    msg.textContent = "Account created. You can log in now.";
    msg.className = "form-message is-success";
    registerForm.reset();
    setTimeout(() => switchTab("login"), 900);
  } catch (err) {
    msg.textContent = err.message;
    msg.className = "form-message is-error";
  }
});

// ---------- logout ----------
el("logout-btn").addEventListener("click", logout);

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
  showAuthView();
}

// ---------- dashboard ----------
async function enterDashboard() {
  showDashboardView();
  el("user-email-badge").textContent = localStorage.getItem(EMAIL_KEY) || "";
  await loadTasks();
  await tryLoadAdminPanel();
}

async function loadTasks() {
  const list = el("task-list");
  const empty = el("empty-state");
  const count = el("task-count");

  let tasks;
  try {
    tasks = await api("/tasks");
  } catch (err) {
    el("task-message").textContent = err.message;
    el("task-message").className = "form-message is-error";
    return;
  }

  list.innerHTML = "";
  if (tasks.length === 0) {
    empty.hidden = false;
    count.textContent = "No tasks yet";
    return;
  }
  empty.hidden = true;
  const doneCount = tasks.filter((t) => t.is_done).length;
  count.textContent = `${doneCount} of ${tasks.length} done`;

  for (const task of tasks) {
    list.appendChild(renderTaskCard(task));
  }
}

function renderTaskCard(task) {
  const li = document.createElement("li");
  li.className = "task-card" + (task.is_done ? " is-done" : "");

  const check = document.createElement("button");
  check.className = "task-check" + (task.is_done ? " is-checked" : "");
  check.setAttribute("aria-label", task.is_done ? "Mark as not done" : "Mark as done");
  check.textContent = task.is_done ? "✓" : "";
  check.addEventListener("click", () => toggleTask(task.id, !task.is_done));

  const title = document.createElement("span");
  title.className = "task-title";
  title.textContent = task.title;

  const del = document.createElement("button");
  del.className = "task-delete";
  del.textContent = "Remove";
  del.addEventListener("click", () => deleteTask(task.id));

  li.append(check, title, del);
  return li;
}

async function toggleTask(id, isDone) {
  try {
    await api(`/tasks/${id}`, { method: "PUT", body: { is_done: isDone } });
    await loadTasks();
  } catch (err) {
    el("task-message").textContent = err.message;
    el("task-message").className = "form-message is-error";
  }
}

async function deleteTask(id) {
  try {
    await api(`/tasks/${id}`, { method: "DELETE" });
    await loadTasks();
  } catch (err) {
    el("task-message").textContent = err.message;
    el("task-message").className = "form-message is-error";
  }
}

el("new-task-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = el("new-task-title");
  const msg = el("task-message");
  msg.textContent = "";
  msg.className = "form-message";

  const title = input.value.trim();
  if (!title) return;

  try {
    await api("/tasks", { method: "POST", body: { title } });
    input.value = "";
    await loadTasks();
  } catch (err) {
    msg.textContent = err.message;
    msg.className = "form-message is-error";
  }
});

// ---------- admin panel (only renders successfully if the user IS an admin) ----------
async function tryLoadAdminPanel() {
  const panel = el("admin-panel");
  const badge = el("admin-badge");
  try {
    const [users, logs] = await Promise.all([
      api("/admin/users"),
      api("/admin/audit-logs"),
    ]);
    badge.hidden = false;
    panel.hidden = false;

    const usersList = el("admin-users-list");
    usersList.innerHTML = "";
    for (const u of users) {
      const li = document.createElement("li");
      li.textContent = `${u.email} — ${u.role}`;
      usersList.appendChild(li);
    }

    const auditList = el("admin-audit-list");
    auditList.innerHTML = "";
    for (const entry of logs.slice(0, 15)) {
      const li = document.createElement("li");
      const when = new Date(entry.created_at).toLocaleString();
      li.innerHTML = `<span class="audit-event">${entry.event_type}</span> — ${entry.user_email || "—"} <br>${when}`;
      auditList.appendChild(li);
    }
  } catch {
    // Not an admin (403) — simply don't show the panel. This is expected
    // for normal users and is not an error state.
    badge.hidden = true;
    panel.hidden = true;
  }
}

// ---------- boot ----------
(function init() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    enterDashboard().catch(() => showAuthView());
  } else {
    showAuthView();
  }
})();
