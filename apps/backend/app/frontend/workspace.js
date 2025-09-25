const transcript = document.getElementById("chat-transcript");
const workspaceForm = document.getElementById("chat-form");
const textInput = document.getElementById("text-input");
const taskSelect = document.getElementById("task-select");
const statusBanner = document.getElementById("status-message");
const workflowIdLabel = document.getElementById("workflow-id");
const workflowTaskLabel = document.getElementById("workflow-task");
const workflowStageLabel = document.getElementById("workflow-stage");
const workflowStatusLabel = document.getElementById("workflow-status");
const resetButton = document.getElementById("reset-workspace");
const metricWorkflows = document.getElementById("metric-workflows");
const metricMessages = document.getElementById("metric-messages");
const metricArtifacts = document.getElementById("metric-artifacts");
const metricApproval = document.getElementById("metric-approvals");
const stageProgressList = document.getElementById("stage-progress");

const apiMeta = document.querySelector('meta[name="api-base-url"]');
const API_ROOT = (apiMeta?.content ?? "").replace(/\/$/, "");
const POLL_BASE_INTERVAL = 1500;
const POLL_MAX_INTERVAL = 5500;

const STAGE_LABELS = {
  route: "Routing",
  ingestion: "Ingestion",
  drafting: "Drafting",
  critique: "Critique",
  revision: "Revision",
  compliance: "Compliance",
  publishing: "Publishing",
  done: "Complete",
};

const STAGE_HINT = {
  route: "Workflow queued",
  ingestion: "Processing uploaded context",
  drafting: "Drafting the next resume output",
  critique: "Reviewing draft quality",
  revision: "Applying requested revisions",
  compliance: "Running compliance checks",
  publishing: "Preparing final artifacts",
  done: "Finalizing response",
};

const STAGE_SEQUENCE = [
  "route",
  "ingestion",
  "drafting",
  "critique",
  "revision",
  "compliance",
  "publishing",
  "done",
];

const conversation = [];
const messageCache = new Set();
const approvalState = { workflowId: null, pendingDecision: false };
const metrics = { workflowsStarted: 0, artifactsDelivered: 0 };
let approvalMetricStatus = "Not requested";
let activeWorkflow = {
  id: null,
  task: null,
  requestId: null,
  stage: null,
  pollController: null,
};

const initialGreeting = {
  role: "assistant",
  content:
    "Share resume context or requests and choose a workflow task. I'll relay it to the Temporal workflow and surface each update the API returns.",
  timestamp: new Date(),
};
conversation.push(initialGreeting);
messageCache.add(createMessageKey(initialGreeting));
renderTranscript();
setStatus("You're ready to start a workflow.", "success");
updateSummary();
setApprovalMetric("Not requested");
refreshMetrics();
renderStageProgress();

workspaceForm?.addEventListener("submit", handleSubmit);
textInput?.addEventListener("input", autoResize);
textInput?.addEventListener("focus", autoResize);
textInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    workspaceForm?.requestSubmit();
  }
});
resetButton?.addEventListener("click", resetWorkspace);

function autoResize() {
  if (!textInput) {
    return;
  }
  textInput.style.height = "auto";
  textInput.style.height = `${Math.min(textInput.scrollHeight, 240)}px`;
}

async function handleSubmit(event) {
  event.preventDefault();
  if (!workspaceForm) {
    return;
  }
  const message = textInput?.value?.trim() ?? "";
  if (!message) {
    setStatus("Add instructions for the workflow first.", "error");
    return;
  }
  const task = taskSelect?.value ?? "resume_pipeline";

  const userMessage = {
    role: "human",
    content: message,
    timestamp: new Date(),
  };
  addMessage(userMessage);

  const requestId = crypto.randomUUID?.() ?? `workspace-${Date.now()}`;
  const payload = createWorkflowPayload({ message, task, requestId });

  try {
    setComposerBusy(true);
    setStatus("Starting workflow...", "pending");
    const response = await startWorkflow(payload);
    activeWorkflow.id = response.workflow_id;
    activeWorkflow.task = task;
    activeWorkflow.requestId = requestId;
    metrics.workflowsStarted += 1;
    refreshMetrics();
    updateSummary({
      workflowId: response.workflow_id,
      task,
      stage: "route",
      status: "in_progress",
    });
    beginPolling(response.workflow_id);
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    setStatus(detail || "Failed to start workflow", "error");
    addMessage({
      role: "system",
      content: "The request did not reach the workflow service. Double-check the API and try again.",
      timestamp: new Date(),
    });
  } finally {
    if (textInput) {
      textInput.value = "";
      autoResize();
    }
    setComposerBusy(false);
  }
}

function addMessage(entry) {
  const key = createMessageKey(entry);
  if (!messageCache.has(key)) {
    messageCache.add(key);
    conversation.push({ ...entry });
    if (entry.type === "artifact") {
      registerArtifact();
    }
    refreshMetrics();
    renderTranscript();
  }
}

function createMessageKey(entry) {
  return `${entry.role}|${entry.content}`;
}

function renderTranscript() {
  if (!transcript) {
    return;
  }
  transcript.innerHTML = "";
  if (!conversation.length) {
    transcript.classList.add("is-empty");
    return;
  }
  transcript.classList.remove("is-empty");
  for (const entry of conversation) {
    transcript.appendChild(createMessageNode(entry));
  }
  transcript.scrollTop = transcript.scrollHeight;
}

function createMessageNode(entry) {
  const article = document.createElement("article");
  const roleClass = entry.role === "assistant" ? "assistant" : entry.role === "system" ? "system" : "user";
  article.className = `message ${roleClass}`;

  const meta = document.createElement("div");
  meta.className = "message__meta";
  const roleLabel = entry.role === "assistant" ? "Assistant" : entry.role === "system" ? "System" : "You";
  meta.appendChild(document.createTextNode(roleLabel));
  const timeStamp = document.createElement("span");
  timeStamp.textContent = formatTimestamp(entry.timestamp);
  meta.appendChild(timeStamp);

  const body = document.createElement("p");
  body.className = "message__body";
  body.textContent = entry.content;
  article.append(meta, body);

  if (entry.detail) {
    const detail = document.createElement("p");
    detail.className = "message__detail";
    detail.textContent = entry.detail;
    article.appendChild(detail);
  }

  return article;
}

function formatTimestamp(value) {
  const date = value ? new Date(value) : new Date();
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function setComposerBusy(isBusy) {
  if (!workspaceForm) {
    return;
  }
  workspaceForm.classList.toggle("is-busy", isBusy);
  const submit = workspaceForm.querySelector("button[type='submit']");
  if (submit) {
    submit.disabled = isBusy;
  }
  if (textInput) {
    textInput.disabled = isBusy;
  }
  if (taskSelect) {
    taskSelect.disabled = isBusy;
  }
}

function createWorkflowPayload({ message, task, requestId }) {
  const artifacts = message ? { notes: message } : {};
  return {
    task,
    request_id: requestId,
    artifacts,
    flags: {
      source: "workspace",
    },
  };
}

async function startWorkflow(payload) {
  const response = await fetchJson(apiUrl("/workflows/resume"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response?.workflow_id) {
    throw new Error("Workflow response did not include an identifier");
  }
  return response;
}

function beginPolling(workflowId) {
  if (activeWorkflow.pollController) {
    activeWorkflow.pollController.abort();
  }
  const controller = new AbortController();
  activeWorkflow.pollController = controller;
  void pollWorkflowState({ workflowId, signal: controller.signal });
}

async function pollWorkflowState({ workflowId, signal }) {
  let attempt = 0;
  let finalState = null;
  while (!signal.aborted) {
    let state = null;
    try {
      state = await fetchWorkflowState(workflowId);
    } catch (error) {
      if (signal.aborted) {
        return;
      }
      setStatus(
        error instanceof Error ? error.message : "Unable to reach the workflow state endpoint.",
        "error",
      );
      addMessage({
        role: "system",
        content: "Polling stopped due to a network error.",
        timestamp: new Date(),
      });
      return;
    }
    if (!state) {
      setStatus("Workflow state unavailable.", "error");
      return;
    }

    applyWorkflowState(state);

    if (state.status === "complete" || state.status === "error") {
      finalState = state;
      break;
    }

    const delay = Math.min(POLL_BASE_INTERVAL + attempt * 400, POLL_MAX_INTERVAL);
    attempt += 1;
    try {
      await wait(delay, signal);
    } catch (error) {
      return;
    }
  }

  if (!finalState || signal.aborted) {
    return;
  }

  if (finalState.status === "complete") {
    try {
      const resultState = await fetchWorkflowResult(workflowId);
      if (resultState) {
        finalState = resultState;
        applyWorkflowState(resultState);
      }
    } catch (error) {
      // continue with latest state
    }
  }

  finalizeWorkflow(finalState);
}

function applyWorkflowState(state) {
  updateSummary({
    workflowId: state.request_id ?? activeWorkflow.id,
    task: state.task,
    stage: state.stage,
    status: state.status,
  });
  syncMessagesFromState(state);
  handleStageTransition(state.stage);

  if (state.flags?.awaiting_human) {
    showApprovalControls(activeWorkflow.id ?? state.request_id);
  } else {
    hideApprovalControls();
  }

  const hint = STAGE_HINT[state.stage];
  if (state.status === "in_progress" && hint) {
    setStatus(hint, "pending");
  }
}

function syncMessagesFromState(state) {
  const messages = Array.isArray(state.messages) ? state.messages : [];
  for (const entry of messages) {
    if (!entry || typeof entry.content !== "string") {
      continue;
    }
    const normalizedRole = entry.role === "human" ? "human" : entry.role === "system" ? "system" : "assistant";
    addMessage({
      role: normalizedRole,
      content: entry.content,
      timestamp: new Date(),
    });
  }

  if (state.status === "error" && state.flags?.human_notes) {
    addMessage({
      role: "system",
      content: "Workflow reported an error.",
      detail: state.flags.human_notes,
      timestamp: new Date(),
    });
  }

  if (state.status === "complete") {
    const artifacts = state.artifacts ?? {};
    if (typeof artifacts.draft_resume === "string" && artifacts.draft_resume.trim()) {
      addMessage({
        role: "assistant",
        content: artifacts.draft_resume.trim(),
        timestamp: new Date(),
        type: "artifact",
      });
    } else if (typeof artifacts.published_resume === "string") {
      addMessage({
        role: "assistant",
        content: artifacts.published_resume.trim(),
        timestamp: new Date(),
        type: "artifact",
      });
    }
  }
}

function handleStageTransition(stage) {
  if (!stage || activeWorkflow.stage === stage) {
    return;
  }
  activeWorkflow.stage = stage;
  renderStageProgress(stage);
  const label = STAGE_LABELS[stage] ?? stage;
  addMessage({
    role: "system",
    content: `Stage updated: ${label}`,
    timestamp: new Date(),
  });
}

function finalizeWorkflow(state) {
  if (state.status === "error") {
    setStatus("Workflow ended with an error.", "error");
  } else {
    setStatus("Workflow completed.", "success");
  }
  setComposerBusy(false);
  activeWorkflow.pollController = null;
}

function showApprovalControls(workflowId) {
  if (!workflowId || approvalState.pendingDecision) {
    return;
  }
  if (approvalState.workflowId === workflowId) {
    return;
  }
  approvalState.workflowId = workflowId;
  setApprovalMetric("Action required");
  setStatus("Workflow is waiting for your approval.", "pending", {
    buttons: [
      {
        label: "Approve",
        variant: "primary",
        onClick: () => void handleApprovalDecision(workflowId, true),
      },
      {
        label: "Request changes",
        onClick: () => void handleApprovalDecision(workflowId, false),
      },
    ],
  });
}

function hideApprovalControls() {
  approvalState.workflowId = null;
  approvalState.pendingDecision = false;
  if (approvalMetricStatus === "Action required") {
    setApprovalMetric("Not requested");
  }
}

async function handleApprovalDecision(workflowId, approved) {
  approvalState.pendingDecision = true;
  setStatus(approved ? "Submitting approval..." : "Requesting changes...", "pending");
  try {
    await submitWorkflowApproval(workflowId, approved);
    approvalState.pendingDecision = false;
    setStatus("Decision submitted.", "success");
    setApprovalMetric(approved ? "Approved" : "Changes requested");
  } catch (error) {
    approvalState.pendingDecision = false;
    approvalState.workflowId = workflowId;
    setStatus(
      error instanceof Error ? error.message : "Failed to submit decision.",
      "error",
      {
        buttons: [
          {
            label: "Retry",
            variant: "primary",
            onClick: () => void handleApprovalDecision(workflowId, approved),
          },
        ],
      },
    );
  }
}

function updateSummary({ workflowId, task, stage, status } = {}) {
  if (workflowIdLabel) {
    workflowIdLabel.textContent = workflowId ?? "Not started";
  }
  if (workflowTaskLabel) {
    workflowTaskLabel.textContent = task ?? "—";
  }
  if (workflowStageLabel) {
    workflowStageLabel.textContent = stage ? STAGE_LABELS[stage] ?? stage : "Waiting";
  }
  if (workflowStatusLabel) {
    workflowStatusLabel.textContent = status ? status.replaceAll("_", " ") : "Idle";
  }
  renderStageProgress(stage);
}

function setStatus(message, variant, actionConfig) {
  if (!statusBanner) {
    return;
  }
  statusBanner.classList.remove("is-success", "is-error", "is-pending");
  statusBanner.replaceChildren();
  if (variant) {
    statusBanner.classList.add(`is-${variant}`);
  }
  statusBanner.append(document.createTextNode(message ?? ""));
  if (actionConfig?.buttons?.length) {
    const actions = document.createElement("span");
    actions.className = "status-banner__actions";
    for (const config of actionConfig.buttons) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "status-banner__button";
      if (config.variant === "primary") {
        button.classList.add("is-primary");
      }
      button.textContent = config.label;
      if (typeof config.onClick === "function") {
        button.addEventListener("click", config.onClick);
      }
      actions.appendChild(button);
    }
    statusBanner.append(actions);
  }
}

async function fetchWorkflowState(workflowId) {
  const response = await fetchJson(apiUrl(`/workflows/${workflowId}`));
  return response?.state ?? null;
}

async function fetchWorkflowResult(workflowId) {
  const response = await fetchJson(apiUrl(`/workflows/${workflowId}/result`));
  return response?.state ?? null;
}

async function submitWorkflowApproval(workflowId, approved) {
  await fetchJson(apiUrl(`/workflows/${workflowId}/approval`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved }),
  });
}

async function fetchJson(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    throw new Error("Network request failed");
  }
  if (!response.ok) {
    let detail;
    try {
      const payload = await response.json();
      detail = payload?.detail ?? payload?.message;
    } catch (error) {
      detail = await response.text();
    }
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  if (response.status === 204) {
    return null;
  }
  try {
    return await response.json();
  } catch (error) {
    throw new Error("Invalid JSON response from server");
  }
}

function apiUrl(path) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_ROOT}${normalized}` || normalized;
}

function wait(duration, signal) {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, duration);
    const onAbort = () => {
      window.clearTimeout(timer);
      reject(new DOMException("Aborted", "AbortError"));
    };
    if (signal) {
      signal.addEventListener("abort", onAbort, { once: true });
    }
  });
}

function resetWorkspace() {
  if (activeWorkflow.pollController) {
    activeWorkflow.pollController.abort();
  }
  activeWorkflow = {
    id: null,
    task: null,
    requestId: null,
    stage: null,
    pollController: null,
  };
  approvalState.workflowId = null;
  approvalState.pendingDecision = false;
  metrics.workflowsStarted = 0;
  metrics.artifactsDelivered = 0;
  conversation.splice(0, conversation.length, initialGreeting);
  messageCache.clear();
  messageCache.add(createMessageKey(initialGreeting));
  renderTranscript();
  updateSummary();
  renderStageProgress();
  setStatus("Workspace cleared.", "success");
  setApprovalMetric("Not requested");
  refreshMetrics();
  if (textInput) {
    textInput.disabled = false;
    textInput.value = "";
    autoResize();
  }
  if (taskSelect) {
    taskSelect.disabled = false;
    taskSelect.value = "ingest";
  }
}

function refreshMetrics() {
  if (metricWorkflows) {
    metricWorkflows.textContent = String(metrics.workflowsStarted);
  }
  if (metricMessages) {
    const total = Math.max(conversation.length - 1, 0);
    metricMessages.textContent = String(total);
  }
  if (metricArtifacts) {
    metricArtifacts.textContent = String(metrics.artifactsDelivered);
  }
}

function registerArtifact() {
  metrics.artifactsDelivered += 1;
}

function setApprovalMetric(value) {
  approvalMetricStatus = value;
  if (metricApproval) {
    metricApproval.textContent = value;
  }
}

function renderStageProgress(stage) {
  if (!stageProgressList) {
    return;
  }
  const stageIndex = stage ? STAGE_SEQUENCE.indexOf(stage) : -1;
  const items = stageProgressList.querySelectorAll("li[data-stage]");
  items.forEach((item) => {
    const itemStage = item.dataset.stage;
    const itemIndex = STAGE_SEQUENCE.indexOf(itemStage);
    const isActive = stageIndex >= 0 && itemStage === stage;
    const isComplete = stageIndex > 0 && itemIndex > -1 && itemIndex < stageIndex;
    item.classList.toggle("is-active", isActive);
    item.classList.toggle("is-complete", isComplete);
    if (isActive) {
      item.setAttribute("aria-current", "step");
    } else {
      item.removeAttribute("aria-current");
    }
  });
}
