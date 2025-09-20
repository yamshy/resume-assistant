const CHAT_API_URL = "/chat";
const KNOWLEDGE_API_URL = "/knowledge";
const GENERATE_API_URL = "/generate";

const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");

const workflowForm = document.getElementById("workflow-form");
const workflowStatus = document.getElementById("workflow-status");
const workflowResult = document.getElementById("workflow-result");
const previewSection = document.getElementById("preview-section");
const clearPreviewButton = document.getElementById("clear-preview");

const toggleButtons = document.querySelectorAll(".panel-toggle-button");
const ingestPanel = document.getElementById("ingest-panel");
const generatePanel = document.getElementById("generate-panel");

const resumeFilesInput = document.getElementById("resume-files");
const ingestNotesInput = document.getElementById("ingest-notes");
const jobDescriptionInput = document.getElementById("job-description");
const validationFollowUp = document.getElementById("validation-follow-up");

let conversationHistory = [];
let workflowMode = "ingest";

function setStatus(element, message, variant = "info") {
  if (!element) {
    return;
  }
  element.textContent = message;
  element.classList.remove("status-success", "status-error");
  if (variant === "success") {
    element.classList.add("status-success");
  } else if (variant === "error") {
    element.classList.add("status-error");
  }
}

function createMessageElement(role, content) {
  const message = document.createElement("section");
  message.classList.add("message", `message-${role}`);

  const roleLabel = document.createElement("span");
  roleLabel.classList.add("message-role");
  roleLabel.textContent = role === "user" ? "You" : role === "assistant" ? "Assistant" : "System";

  const text = document.createElement("p");
  text.classList.add("message-content");
  text.textContent = content;

  message.append(roleLabel, text);
  return message;
}

function appendMessage(role, content) {
  const element = createMessageElement(role, content);
  chatLog.appendChild(element);
  chatLog.scrollTo({ top: chatLog.scrollHeight, behavior: "smooth" });
}

function clearPreview() {
  if (workflowResult) {
    workflowResult.textContent = "";
  }
  if (previewSection) {
    previewSection.hidden = true;
  }
}

function showPreview(payload) {
  if (!workflowResult || !previewSection) {
    return;
  }
  workflowResult.textContent = payload;
  previewSection.hidden = false;
}

function setWorkflowMode(mode) {
  workflowMode = mode;
  toggleButtons.forEach((button) => {
    const isActive = button.dataset.mode === mode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });

  if (ingestPanel) {
    const active = mode === "ingest";
    ingestPanel.classList.toggle("is-active", active);
    ingestPanel.hidden = !active;
    if (resumeFilesInput) {
      if (active) {
        resumeFilesInput.setAttribute("required", "required");
      } else {
        resumeFilesInput.removeAttribute("required");
      }
    }
  }

  if (generatePanel) {
    const active = mode === "generate";
    generatePanel.classList.toggle("is-active", active);
    generatePanel.hidden = !active;
    if (jobDescriptionInput) {
      if (active) {
        jobDescriptionInput.setAttribute("required", "required");
      } else {
        jobDescriptionInput.removeAttribute("required");
      }
    }
  }

  setStatus(workflowStatus, "");
}

async function requestAssistantReply(message) {
  const payloadHistory = [...conversationHistory];
  appendMessage("user", message);

  try {
    const response = await fetch(CHAT_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        history: payloadHistory,
      }),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    const reply = data.reply ?? data.message ?? data.response ?? "The assistant returned an empty response.";

    appendMessage("assistant", reply);

    if (Array.isArray(data.history)) {
      conversationHistory = data.history;
    } else {
      conversationHistory = [
        ...payloadHistory,
        { role: "user", content: message },
        { role: "assistant", content: reply },
      ];
    }
  } catch (error) {
    const reason = error instanceof Error ? error.message : "Unknown error";
    appendMessage("system", reason);
  }
}

async function sendMessage(event) {
  event.preventDefault();
  const message = messageInput?.value.trim();
  if (!message) {
    return;
  }
  if (messageInput) {
    messageInput.value = "";
  }
  await requestAssistantReply(message);
}

async function handleWorkflowSubmit(event) {
  event.preventDefault();
  if (workflowMode === "ingest") {
    await processIngestion();
  } else {
    await processGeneration();
  }
}

async function processIngestion() {
  const files = resumeFilesInput?.files;
  if (!files || files.length === 0) {
    setStatus(workflowStatus, "Select at least one resume to ingest.", "error");
    return;
  }

  const formData = new FormData();
  Array.from(files).forEach((file) => {
    formData.append("resumes", file);
  });

  const notes = ingestNotesInput?.value.trim();
  if (notes) {
    formData.append("notes", notes);
  }

  clearPreview();
  setStatus(workflowStatus, "Processing resumes...");

  try {
    const response = await fetch(KNOWLEDGE_API_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    const summary = data.summary ?? "Resumes ingested successfully.";
    setStatus(workflowStatus, summary, "success");

    if (workflowResult) {
      const snapshot = data.profile_snapshot ?? {};
      const rendered = Object.keys(snapshot).length ? JSON.stringify(snapshot, null, 2) : JSON.stringify(data, null, 2);
      showPreview(rendered);
    }

    if (resumeFilesInput) {
      resumeFilesInput.value = "";
    }
    if (ingestNotesInput) {
      ingestNotesInput.value = "";
    }

    const skills = Array.isArray(data.skills_indexed) ? data.skills_indexed.slice(0, 5) : [];
    const skillsLine = skills.length ? skills.join(", ") : "no new skills";
    const followUp = `I just ingested ${data.ingested ?? "several"} resumes. Highlight the key checks we should perform on the structured skills (${skillsLine}).`;
    await requestAssistantReply(followUp);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to ingest resumes.";
    setStatus(workflowStatus, message, "error");
  }
}

async function processGeneration() {
  const jobDescription = jobDescriptionInput?.value.trim();
  if (!jobDescription) {
    setStatus(workflowStatus, "Paste a job description to generate a resume.", "error");
    return;
  }

  clearPreview();
  setStatus(workflowStatus, "Generating resume...");

  try {
    const response = await fetch(GENERATE_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        job_posting: jobDescription,
      }),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    setStatus(workflowStatus, "Resume generated successfully.", "success");
    showPreview(JSON.stringify(data, null, 2));

    if (validationFollowUp?.checked) {
      const firstLine = jobDescription.split("\n").find((line) => line.trim()) ?? jobDescription;
      const snippet = firstLine.trim().slice(0, 140);
      const followUp = `We generated a resume for this role: "${snippet}". Provide a validation checklist before I send it.`;
      await requestAssistantReply(followUp);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to generate resume.";
    setStatus(workflowStatus, message, "error");
  }
}

if (chatForm) {
  chatForm.addEventListener("submit", sendMessage);
}

if (workflowForm) {
  workflowForm.addEventListener("submit", handleWorkflowSubmit);
}

if (toggleButtons.length) {
  toggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const mode = button.dataset.mode;
      if (mode && mode !== workflowMode) {
        setWorkflowMode(mode);
      }
    });
  });
}

if (clearPreviewButton) {
  clearPreviewButton.addEventListener("click", clearPreview);
}

if (chatLog) {
  const welcomeMessage =
    "Hi! I'm your resume assistant. Upload a few resumes, then paste a job description and I'll help tailor and validate your résumé.";
  appendMessage("assistant", welcomeMessage);
  conversationHistory.push({ role: "assistant", content: welcomeMessage });
}

setWorkflowMode(workflowMode);
