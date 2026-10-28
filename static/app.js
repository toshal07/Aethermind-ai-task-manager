const $ = (selector) => document.querySelector(selector);
const extractForm = $("#extract-form");
const taskInput = $("#task-input");
const extractButton = $("#extract-button");
const previewSection = $("#preview-section");
const previewForm = $("#preview-form");
const saveButton = $("#save-button");
const taskList = $("#task-list");
const statusFilter = $("#status-filter");
let previewData = null;
let toastTimer = null;

function showToast(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3500);
}

async function api(url, options = {}) {
  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) }
    });
  } catch {
    throw new Error("Could not connect to the server. Check your internet connection or backend.");
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body.detail;
    throw new Error(Array.isArray(detail) ? detail.map(item => item.msg).join(", ") : (detail || "Request failed."));
  }
  return body;
}

function setBusy(button, busy, busyText, normalText) {
  button.disabled = busy;
  if (busy) {
    button.dataset.originalText = button.innerHTML;
    button.textContent = busyText;
  } else {
    button.innerHTML = button.dataset.originalText || normalText;
  }
}

function populatePreview(data) {
  previewData = data;
  $("#preview-title").value = data.title || "";
  $("#preview-description").value = data.description || "";
  $("#preview-deadline").value = data.deadline || "";
  $("#preview-priority").value = data.priority || "Medium";
  $("#preview-category").value = data.category || "Personal";
  previewSection.classList.remove("hidden");
  previewSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

extractForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = taskInput.value.trim();
  if (text.length < 8) {
    showToast("Please describe your task in at least 8 characters.", true);
    return;
  }
  setBusy(extractButton, true, "Extracting…", "✦ Extract with AI →");
  try {
    const result = await api("/api/extract", {
      method: "POST",
      body: JSON.stringify({ text })
    });
    populatePreview(result.preview);
    showToast("AI extraction complete. Review the fields before saving.");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    setBusy(extractButton, false, false, "✦ Extract with AI →");
  }
});

previewForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const task = {
    title: $("#preview-title").value.trim(),
    description: $("#preview-description").value.trim(),
    deadline: $("#preview-deadline").value || null,
    priority: $("#preview-priority").value,
    category: $("#preview-category").value.trim() || "Personal"
  };
  if (task.title.length < 3) {
    showToast("Task title must contain at least 3 characters.", true);
    return;
  }
  setBusy(saveButton, true, "Saving…", "Confirm & save task →");
  try {
    const result = await api("/api/tasks", {
      method: "POST",
      body: JSON.stringify(task)
    });
    previewSection.classList.add("hidden");
    taskInput.value = "";
    previewData = null;
    showToast(result.message || "Task saved.");
    await loadTasks();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    setBusy(saveButton, false, false, "Confirm & save task →");
  }
});

$("#cancel-preview").addEventListener("click", () => {
  previewSection.classList.add("hidden");
  previewData = null;
  showToast("Preview discarded. Nothing was saved.");
});

$("#refresh-button").addEventListener("click", loadTasks);
statusFilter.addEventListener("change", loadTasks);

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  })[char]);
}

function formatDate(value) {
  if (!value) return "No deadline";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function renderTasks(tasks) {
  $("#stat-total").textContent = tasks.length;
  $("#stat-progress").textContent = tasks.filter(task => task.status === "In Progress").length;
  $("#stat-completed").textContent = tasks.filter(task => task.status === "Completed").length;

  const filter = statusFilter.value;
  const visible = filter === "All" ? tasks : tasks.filter(task => task.status === filter);
  if (!visible.length) {
    taskList.innerHTML = `<div class="empty-state"><strong>${filter === "All" ? "Your workspace is ready." : "No tasks in this view."}</strong><p>${filter === "All" ? "Describe a task above and let AI help organize it." : "Choose another filter or update a task status."}</p></div>`;
    return;
  }

  taskList.innerHTML = visible.map(task => {
    const priorityClass = `priority-${String(task.priority).toLowerCase()}`;
    return `<article class="task-card">
      <div>
        <div class="task-title-line">
          <h4 class="task-title">${escapeHtml(task.title)}</h4>
          <span class="meta-chip priority ${priorityClass}">${escapeHtml(task.priority)} priority</span>
        </div>
        ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ""}
        <div class="task-meta">
          <span class="meta-chip">◷ ${escapeHtml(formatDate(task.deadline))}</span>
          <span class="meta-chip">${escapeHtml(task.category || "Personal")}</span>
          <span class="meta-chip">Created ${escapeHtml(String(task.created_at || "").slice(0, 10))}</span>
        </div>
      </div>
      <div class="task-actions">
        <select class="status-select" aria-label="Update status for ${escapeHtml(task.title)}" data-status-id="${task.id}">
          ${["Pending", "In Progress", "Completed"].map(status => `<option ${task.status === status ? "selected" : ""}>${status}</option>`).join("")}
        </select>
        <button class="delete-button" type="button" data-delete-id="${task.id}" aria-label="Delete ${escapeHtml(task.title)}">Delete</button>
      </div>
    </article>`;
  }).join("");

  taskList.querySelectorAll("[data-status-id]").forEach(select => {
    select.addEventListener("change", async () => {
      try {
        const result = await api(`/api/tasks/${select.dataset.statusId}`, {
          method: "PATCH", body: JSON.stringify({ status: select.value })
        });
        showToast(result.message);
        await loadTasks();
      } catch (error) {
        showToast(error.message, true);
        await loadTasks();
      }
    });
  });

  taskList.querySelectorAll("[data-delete-id]").forEach(button => {
    button.addEventListener("click", async () => {
      if (!window.confirm("Delete this task permanently?")) return;
      try {
        const result = await api(`/api/tasks/${button.dataset.deleteId}`, { method: "DELETE" });
        showToast(result.message);
        await loadTasks();
      } catch (error) {
        showToast(error.message, true);
      }
    });
  });
}

async function loadTasks() {
  taskList.innerHTML = '<div class="loading-state">Loading your workspace…</div>';
  try {
    const tasks = await api("/api/tasks");
    renderTasks(tasks);
  } catch (error) {
    taskList.innerHTML = `<div class="empty-state"><strong>Could not load tasks.</strong><p>${escapeHtml(error.message)}</p></div>`;
  }
}

function setGreeting() {
  const hour = new Date().getHours();
  $("#greeting").textContent = hour < 12 ? "Good morning." : hour < 18 ? "Good afternoon." : "Good evening.";
}
setGreeting();
loadTasks();
