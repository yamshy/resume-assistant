const CHAT_API_URL = "/chat";
const KNOWLEDGE_API_URL = "/knowledge";
const GENERATE_API_URL = "/generate";

const MODE_CHAT = "chat";
const MODE_INGEST = "ingest";
const MODE_GENERATE = "generate";

const chatLog = document.getElementById("chat-log");
const interactionForm = document.getElementById("interaction-form");
const statusMessage = document.getElementById("status-message");

const modeButtons = document.querySelectorAll(".mode-button");
const composerSections = document.querySelectorAll(".composer-section");

const chatInput = document.getElementById("chat-input");
const resumeFilesInput = document.getElementById("resume-files");
const ingestNotesInput = document.getElementById("ingest-notes");
const jobDescriptionInput = document.getElementById("job-description");
const validationFollowUp = document.getElementById("validation-follow-up");

let activeMode = MODE_CHAT;
let conversationHistory = [];

function setStatus(message, variant = "info") {
  if (!statusMessage) {
    return;
  }

  statusMessage.textContent = message;
  statusMessage.classList.remove("status-success", "status-error");

  if (!message) {
    return;
  }

  if (variant === "success") {
    statusMessage.classList.add("status-success");
  } else if (variant === "error") {
    statusMessage.classList.add("status-error");
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
  if (!chatLog) {
    return;
  }
  const element = createMessageElement(role, content);
  chatLog.appendChild(element);
  chatLog.scrollTo({ top: chatLog.scrollHeight, behavior: "smooth" });
}

function appendStructuredMessage(label, payload) {
  if (!chatLog) {
    return;
  }

  const wrapper = document.createElement("section");
  wrapper.classList.add("message", "message-structured");

  const header = document.createElement("header");
  header.classList.add("structured-header");

  const title = document.createElement("span");
  title.classList.add("message-role");
  title.textContent = label;

  header.appendChild(title);
  wrapper.appendChild(header);

  const body = document.createElement("pre");
  body.classList.add("structured-content");

  if (typeof payload === "string") {
    body.textContent = payload;
  } else {
    body.textContent = JSON.stringify(payload, null, 2);
  }

  wrapper.appendChild(body);
  chatLog.appendChild(wrapper);
  chatLog.scrollTo({ top: chatLog.scrollHeight, behavior: "smooth" });
}

function setMode(mode) {
  activeMode = mode;

  modeButtons.forEach((button) => {
    const isActive = button.dataset.mode === mode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });

  composerSections.forEach((section) => {
    const isActive = section.dataset.mode === mode;
    section.classList.toggle("is-active", isActive);
    section.hidden = !isActive;
  });

  if (chatInput) {
    if (mode === MODE_CHAT) {
      chatInput.setAttribute("required", "required");
    } else {
      chatInput.removeAttribute("required");
    }
  }

  if (resumeFilesInput) {
    if (mode === MODE_INGEST) {
      resumeFilesInput.setAttribute("required", "required");
    } else {
      resumeFilesInput.removeAttribute("required");
    }
  }

  if (jobDescriptionInput) {
    if (mode === MODE_GENERATE) {
      jobDescriptionInput.setAttribute("required", "required");
    } else {
      jobDescriptionInput.removeAttribute("required");
    }
  }

  setStatus("");
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

async function sendChatMessage() {
  const message = chatInput?.value.trim();
  if (!message) {
    setStatus("Enter a message to chat with the assistant.", "error");
    return;
  }

  if (chatInput) {
    chatInput.value = "";
  }

  setStatus("");
  await requestAssistantReply(message);
}

async function processIngestion() {
  const files = resumeFilesInput?.files;
  if (!files || files.length === 0) {
    setStatus("Select at least one resume to ingest.", "error");
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

  setStatus("Processing resumes...");

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

    appendMessage("system", summary);

    const snapshot = data.profile_snapshot;
    if (snapshot && typeof snapshot === "object" && Object.keys(snapshot).length > 0) {
      appendStructuredMessage("Ingestion snapshot", snapshot);
    } else {
      appendStructuredMessage("Ingestion response", data);
    }

    setStatus("Resumes ingested successfully.", "success");

    if (resumeFilesInput) {
      resumeFilesInput.value = "";
    }
    if (ingestNotesInput) {
      ingestNotesInput.value = "";
    }

    const skills = Array.isArray(data.skills_indexed) ? data.skills_indexed.slice(0, 5) : [];
    const skillsLine = skills.length ? skills.join(", ") : "no new skills";
    const followUp = `I just ingested ${data.ingested ?? files.length} resumes. Highlight the key checks we should perform on the structured skills (${skillsLine}).`;
    await requestAssistantReply(followUp);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to ingest resumes.";
    setStatus(message, "error");
    appendMessage("system", message);
  }
}

async function processGeneration() {
  const jobDescription = jobDescriptionInput?.value.trim();
  if (!jobDescription) {
    setStatus("Paste a job description to generate a resume.", "error");
    return;
  }

  setStatus("Generating resume...");

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
    appendMessage("system", "Resume generated successfully.");
    appendStructuredMessage("Generated resume", data);

    setStatus("Resume generated successfully.", "success");

    if (validationFollowUp?.checked) {
      const firstLine = jobDescription.split("\n").find((line) => line.trim()) ?? jobDescription;
      const snippet = firstLine.trim().slice(0, 140);
      const followUp = `We generated a resume for this role: "${snippet}". Provide a validation checklist before I send it.`;
      await requestAssistantReply(followUp);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to generate resume.";
    setStatus(message, "error");
    appendMessage("system", message);
  }
}

async function handleSubmit(event) {
  event.preventDefault();

  if (activeMode === MODE_CHAT) {
    await sendChatMessage();
  } else if (activeMode === MODE_INGEST) {
    await processIngestion();
  } else if (activeMode === MODE_GENERATE) {
    await processGeneration();
  }
}

if (interactionForm) {
  interactionForm.addEventListener("submit", handleSubmit);
}

if (modeButtons.length) {
  modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const mode = button.dataset.mode;
      if (mode && mode !== activeMode) {
        setMode(mode);

        if (mode === MODE_CHAT && chatInput) {
          chatInput.focus();
        } else if (mode === MODE_INGEST && resumeFilesInput) {
          resumeFilesInput.focus();
        } else if (mode === MODE_GENERATE && jobDescriptionInput) {
          jobDescriptionInput.focus();
        }
      }
    });
  });
}

if (chatLog) {
  const welcomeMessage =
    "Hi! I'm your resume assistant. Upload resumes, generate tailored drafts, and keep the validation conversation going here.";
  appendMessage("assistant", welcomeMessage);
  conversationHistory.push({ role: "assistant", content: welcomeMessage });
}

setMode(activeMode);
