const transcript = document.getElementById("chat-transcript");
const workspaceForm = document.getElementById("chat-form");
const textInput = document.getElementById("text-input");
const fileInput = document.getElementById("resume-upload");
const dropZone = document.getElementById("drop-zone");
const uploadButton = document.getElementById("upload-resumes");
const selectedFilesList = document.getElementById("selected-files");
const statusMessage = document.getElementById("status-message");
const modeButtons = document.querySelectorAll(".mode-toggle__option");
const workflowButton = workspaceForm?.querySelector("[data-action='workflow']") ?? null;
const chatButton = workspaceForm?.querySelector("[data-action='chat']") ?? null;
const composerHint = document.getElementById("composer-hint");
const dropLabel = document.querySelector("[data-mode-label]");

const knowledgeUploadFallbackMessage =
  "Something went wrong while ingesting resumes. Double-check the files and try again.";
const missingOpenAIKeyNote = "Set the OPENAI_API_KEY environment variable to enable resume ingestion.";

let uploadConfigurationNote = null;

const initialGreeting =
  "Welcome! Use Ingestion to upload resumes or paste highlights so I can learn your story. Switch to Generation when you're ready for a tailored draft, and feel free to chat with me any time.";

const conversationHistory = [{ role: "assistant", content: initialGreeting }];
let sessionState = null;
let lastProfileDigest = null;
let currentMode = "ingest";
let pendingFiles = [];
let fileSequence = 0;

const modeConfig = {
  ingest: {
    dropLabel: "Drop resumes or click to upload",
    placeholder: "Paste resume updates or describe recent achievements...",
    hint: "Tip: Add multiple resumes or type a quick update to grow your knowledge base.",
    primaryLabel: "Ingest content",
    buttonLabel: "Browse resumes",
  },
  generate: {
    dropLabel: "Drop a job posting or click to upload",
    placeholder: "Paste the job description or outline the role you're targeting...",
    hint: "Tip: The assistant blends your profile with the job description to craft a draft resume.",
    primaryLabel: "Generate resume",
    buttonLabel: "Browse posting",
  },
};

function appendTranscriptMessage(role, text, options = {}) {
  if (!transcript) {
    return null;
  }

  const article = document.createElement("article");
  article.className = `message ${role}`;

  const label = document.createElement("div");
  label.className = "message-role";
  label.textContent = role === "user" ? "You" : role === "assistant" ? "Assistant" : "Update";

  const body = document.createElement("p");
  body.textContent = text;

  article.append(label, body);

  if (options.detailElement) {
    article.appendChild(options.detailElement);
  }

  transcript.appendChild(article);
  transcript.scrollTop = transcript.scrollHeight;
  return article;
}

function getErrorMessage(error) {
  if (!error) {
    return "";
  }
  if (typeof error === "string") {
    return error.trim();
  }
  if (typeof error.message === "string") {
    return error.message.trim();
  }
  return "";
}

function mentionsMissingOpenAIKey(message) {
  if (!message) {
    return false;
  }
  const normalized = message.toLowerCase();
  return normalized.includes("openai api key") || normalized.includes("openai_api_key");
}

function showUploadConfigurationNote(message) {
  if (!workspaceForm) {
    return;
  }
  if (!uploadConfigurationNote) {
    uploadConfigurationNote = document.createElement("p");
    uploadConfigurationNote.className = "upload-configuration-note";
    if (composerHint) {
      workspaceForm.insertBefore(uploadConfigurationNote, composerHint);
    } else {
      workspaceForm.appendChild(uploadConfigurationNote);
    }
  }
  uploadConfigurationNote.textContent = message;
}

function hideUploadConfigurationNote() {
  if (uploadConfigurationNote?.parentElement) {
    uploadConfigurationNote.parentElement.removeChild(uploadConfigurationNote);
  }
  uploadConfigurationNote = null;
}

function createResultCard(title, content) {
  const card = document.createElement("div");
  card.className = "result-card";

  if (title) {
    const heading = document.createElement("h3");
    heading.textContent = title;
    card.appendChild(heading);
  }

  if (typeof content === "string") {
    const paragraph = document.createElement("p");
    paragraph.textContent = content;
    card.appendChild(paragraph);
  } else if (content && typeof content === "object") {
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(content, null, 2);
    card.appendChild(pre);
  }

  return card;
}

function setStatus(message, state) {
  if (!statusMessage) {
    return;
  }
  statusMessage.textContent = message;
  statusMessage.classList.remove("is-success", "is-error", "is-pending");
  if (state) {
    statusMessage.classList.add(`is-${state}`);
  }
}

async function postJSON(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await parseErrorMessage(response);
    throw new Error(detail);
  }
  return response.json();
}

async function postForm(url, formData) {
  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const detail = await parseErrorMessage(response);
    throw new Error(detail);
  }
  return response.json();
}

async function parseErrorMessage(response) {
  try {
    const payload = await response.json();
    if (payload.detail) {
      if (typeof payload.detail === "string") {
        return payload.detail;
      }
      if (Array.isArray(payload.detail) && payload.detail[0]?.msg) {
        return payload.detail[0].msg;
      }
    }
  } catch (error) {
    // Ignore JSON parsing errors and fall back to text.
  }
  try {
    return await response.text();
  } catch (error) {
    return response.statusText || "Request failed";
  }
}

function maybeShowProfileSnapshot(profile) {
  if (!profile || !transcript) {
    return;
  }
  const digest = JSON.stringify(profile);
  if (digest === lastProfileDigest) {
    return;
  }
  lastProfileDigest = digest;
  const card = createResultCard("Profile snapshot", profile);
  appendTranscriptMessage("assistant", "Here's the profile I'm working with right now.", {
    detailElement: card,
  });
}

async function handleChatMessage(message) {
  appendTranscriptMessage("user", message);
  conversationHistory.push({ role: "user", content: message });

  setStatus("Thinking through your request...", "pending");

  try {
    const requestPayload = {
      messages: conversationHistory.map((entry) => {
        const payload = { role: entry.role, content: entry.content };
        if (entry.metadata) {
          payload.metadata = entry.metadata;
        }
        return payload;
      }),
    };
    if (sessionState) {
      requestPayload.session = sessionState;
    }

    const payload = await postJSON("/chat", requestPayload);
    const assistantMessage = payload?.reply?.content || "I'm here to help.";
    const metadata = payload?.reply?.metadata || null;
    const options = {};
    if (metadata && Object.keys(metadata).length > 0) {
      options.detailElement = createResultCard("Assistant context", metadata);
    }
    appendTranscriptMessage("assistant", assistantMessage, options);
    const assistantEntry = { role: "assistant", content: assistantMessage };
    if (metadata) {
      assistantEntry.metadata = metadata;
    }
    conversationHistory.push(assistantEntry);

    sessionState = payload?.session || sessionState;
    maybeShowProfileSnapshot(payload?.profile_snapshot);
    setStatus("Conversation updated.", "success");
  } catch (error) {
    appendTranscriptMessage("system", "I couldn't reach the chat endpoint. Please try again.");
    setStatus(`Chat failed: ${error.message}`, "error");
  }
}

async function handleGenerationRequest(displayMessage, jobDescription) {
  appendTranscriptMessage("user", displayMessage);
  setStatus("Generating a tailored resume...", "pending");

  try {
    const resume = await postJSON("/generate", { job_posting: jobDescription });
    const card = createResultCard("Generated resume", resume);
    appendTranscriptMessage(
      "assistant",
      "Here's a structured resume draft based on the job description.",
      { detailElement: card },
    );
    setStatus("Resume generated.", "success");
  } catch (error) {
    appendTranscriptMessage(
      "system",
      "I couldn't generate a resume. Upload resumes to the knowledge base or try again with more detail.",
    );
    setStatus(`Generation failed: ${error.message}`, "error");
  }
}

async function handleKnowledgeUpload(files, options = {}) {
  if (!files.length) {
    return false;
  }

  const summaryMessage = options.summaryMessage || buildDefaultIngestionSummary(files);
  appendTranscriptMessage("user", summaryMessage);

  const formData = new FormData();
  files.forEach((file) => {
    formData.append("resumes", file, file.name || "resume.txt");
  });
  if (options.notes) {
    formData.append("notes", options.notes);
  }

  setStatus("Processing resumes...", "pending");

  try {
    const result = await postForm("/knowledge", formData);
    const ingestedCount = result.ingested ?? 0;
    const skills = Array.isArray(result.skills_indexed) ? result.skills_indexed : [];
    const achievements = result.achievements_indexed ?? 0;

    const summaryParts = [
      `Processed ${ingestedCount} resume${ingestedCount === 1 ? "" : "s"}.`,
      skills.length
        ? `Indexed ${skills.length} new skill${skills.length === 1 ? "" : "s"}.`
        : "No brand new skills were detected this round.",
      `Captured ${achievements} achievement${achievements === 1 ? "" : "s"}.`,
    ];

    const detailCard = document.createElement("div");
    detailCard.className = "result-card";

    const skillsParagraph = document.createElement("p");
    skillsParagraph.textContent = skills.length
      ? `New skills captured: ${skills.join(", ")}`
      : "No new skills detected in this upload.";
    detailCard.appendChild(skillsParagraph);

    const achievementsParagraph = document.createElement("p");
    achievementsParagraph.textContent = `Achievements captured: ${achievements}`;
    detailCard.appendChild(achievementsParagraph);

    appendTranscriptMessage("assistant", summaryParts.join(" "), { detailElement: detailCard });

    maybeShowProfileSnapshot(result.profile_snapshot);
    setStatus("Resumes ingested successfully.", "success");
    hideUploadConfigurationNote();
    return true;
  } catch (error) {
    const errorMessage = getErrorMessage(error);
    const displayMessage = errorMessage || knowledgeUploadFallbackMessage;

    appendTranscriptMessage("system", displayMessage);
    setStatus(`Ingestion failed: ${displayMessage}`, "error");

    if (mentionsMissingOpenAIKey(displayMessage)) {
      showUploadConfigurationNote(missingOpenAIKeyNote);
    } else {
      hideUploadConfigurationNote();
    }
    return false;
  }
}

function buildDefaultIngestionSummary(files) {
  if (!files.length) {
    return "Sharing resume updates for ingestion.";
  }
  if (files.length === 1) {
    const name = files[0].name || "resume";
    return `Uploaded ${name} for ingestion.`;
  }
  const names = files.map((file) => file.name || "resume");
  return `Uploaded ${files.length} files: ${names.join(", ")}.`;
}

function setMode(mode) {
  if (!modeConfig[mode]) {
    return;
  }
  currentMode = mode;

  modeButtons.forEach((button) => {
    const isActive = button.dataset.mode === mode;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  if (dropLabel) {
    dropLabel.textContent = modeConfig[mode].dropLabel;
  }
  if (textInput) {
    textInput.placeholder = modeConfig[mode].placeholder;
  }
  if (composerHint) {
    composerHint.textContent = modeConfig[mode].hint;
  }
  if (workflowButton) {
    workflowButton.textContent = modeConfig[mode].primaryLabel;
  }
  if (uploadButton) {
    uploadButton.textContent = modeConfig[mode].buttonLabel;
  }
  if (dropZone) {
    dropZone.dataset.mode = mode;
  }
  if (fileInput) {
    fileInput.multiple = mode === "ingest";
  }
}

function addFiles(files) {
  const additions = Array.from(files || []);
  if (!additions.length) {
    return;
  }
  additions.forEach((file) => {
    if (!(file instanceof File)) {
      return;
    }
    pendingFiles.push({ id: `file-${Date.now()}-${fileSequence++}`, file });
  });
  updateSelectedFilesList();
  setStatus(`${pendingFiles.length} file${pendingFiles.length === 1 ? "" : "s"} ready.`, "success");
}

function removeFile(id) {
  pendingFiles = pendingFiles.filter((entry) => entry.id !== id);
  updateSelectedFilesList();
}

function updateSelectedFilesList() {
  if (!selectedFilesList) {
    return;
  }
  selectedFilesList.innerHTML = "";
  pendingFiles.forEach((entry) => {
    const listItem = document.createElement("li");
    listItem.textContent = `${entry.file.name || "untitled"} (${formatFileSize(entry.file.size)})`;

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.setAttribute("aria-label", `Remove ${entry.file.name || "file"}`);
    removeButton.textContent = "×";
    removeButton.addEventListener("click", () => {
      removeFile(entry.id);
    });

    listItem.appendChild(removeButton);
    selectedFilesList.appendChild(listItem);
  });
}

function clearPendingFiles() {
  pendingFiles = [];
  if (fileInput) {
    fileInput.value = "";
  }
  updateSelectedFilesList();
}

function formatFileSize(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "0 KB";
  }
  const size = bytes / 1024;
  if (size < 1024) {
    return `${size.toFixed(1)} KB`;
  }
  return `${(size / 1024).toFixed(1)} MB`;
}

function setComposerBusy(isBusy) {
  if (!workspaceForm) {
    return;
  }
  workspaceForm.classList.toggle("is-busy", isBusy);
  if (workflowButton) {
    workflowButton.disabled = isBusy;
  }
  if (chatButton) {
    chatButton.disabled = isBusy;
  }
  if (uploadButton) {
    uploadButton.disabled = isBusy;
  }
  if (textInput) {
    textInput.disabled = isBusy;
  }
  if (fileInput) {
    fileInput.disabled = isBusy;
  }
}

function buildIngestionSummary(files, notes) {
  const existingFiles = files.map((entry) => entry.file);
  if (!existingFiles.length && !notes) {
    return "Sharing resume updates for ingestion.";
  }

  const parts = [];
  if (existingFiles.length === 1) {
    parts.push(`Uploaded ${existingFiles[0].name || "a resume"} for ingestion.`);
  } else if (existingFiles.length > 1) {
    const names = existingFiles.map((file) => file.name || "resume");
    parts.push(`Uploaded ${existingFiles.length} files: ${names.join(", ")}.`);
  }
  if (notes) {
    const snippet = truncateText(notes).replace(/\s+/g, " ");
    parts.push(`Included typed updates: "${snippet}".`);
  }
  return parts.join(" ") || "Sharing resume updates for ingestion.";
}

function buildGenerationSummary(files, notes) {
  const existingFiles = files.map((entry) => entry.file);
  const parts = [];
  if (existingFiles.length === 1) {
    parts.push(`Uploaded ${existingFiles[0].name || "a job posting"} for generation.`);
  } else if (existingFiles.length > 1) {
    const names = existingFiles.map((file) => file.name || "job posting");
    parts.push(`Uploaded ${existingFiles.length} postings: ${names.join(", ")}.`);
  }
  if (notes) {
    const snippet = truncateText(notes).replace(/\s+/g, " ");
    parts.push(`Shared job description details: "${snippet}".`);
  }
  if (!parts.length) {
    return "Provided a job description for generation.";
  }
  return parts.join(" ");
}

async function readFilesAsText(files) {
  const results = [];
  for (const entry of files) {
    try {
      const text = await entry.file.text();
      const cleaned = text.trim();
      if (cleaned) {
        results.push({
          name: entry.file.name || "uploaded.txt",
          text: cleaned,
        });
      }
    } catch (error) {
      console.error("Failed to read file", entry.file.name, error);
    }
  }
  return results;
}

function truncateText(text, length = 140) {
  if (text.length <= length) {
    return text;
  }
  return `${text.slice(0, length - 1)}…`;
}

if (uploadButton && fileInput) {
  uploadButton.addEventListener("click", () => {
    fileInput.click();
  });
}

if (fileInput) {
  fileInput.addEventListener("change", () => {
    addFiles(fileInput.files);
    fileInput.value = "";
  });
}

if (dropZone && fileInput) {
  dropZone.addEventListener("click", () => {
    if (dropZone.classList.contains("is-disabled")) {
      return;
    }
    fileInput.click();
  });
  dropZone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      fileInput.click();
    }
  });
  dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("is-active");
  });
  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("is-active");
  });
  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.classList.remove("is-active");
    addFiles(event.dataTransfer?.files || []);
  });
}

modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const mode = button.dataset.mode;
    if (mode && mode !== currentMode) {
      setMode(mode);
      setStatus("", null);
    }
  });
});

if (workspaceForm) {
  workspaceForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const submitter = event.submitter;
    const action = submitter?.dataset.action || "workflow";
    const rawMessage = textInput?.value ?? "";
    const message = rawMessage.trim();

    if (action === "chat") {
      if (!message) {
        setStatus("Add a message to chat with the assistant.", "error");
        return;
      }
      if (textInput) {
        textInput.value = "";
      }
      setComposerBusy(true);
      try {
        await handleChatMessage(message);
      } finally {
        setComposerBusy(false);
      }
      return;
    }

    if (currentMode === "ingest") {
      if (!pendingFiles.length && !message) {
        setStatus("Add resumes or paste updates before ingesting.", "error");
        return;
      }
      const filesToUpload = pendingFiles.map((entry) => entry.file);
      if (message) {
        const pseudoFile = new File([message], `pasted-resume-${Date.now()}.txt`, { type: "text/plain" });
        filesToUpload.push(pseudoFile);
      }
      const summaryMessage = buildIngestionSummary(pendingFiles, message);
      setComposerBusy(true);
      try {
        const success = await handleKnowledgeUpload(filesToUpload, {
          notes: message,
          summaryMessage,
        });
        if (success) {
          if (textInput) {
            textInput.value = "";
          }
          clearPendingFiles();
        }
      } finally {
        setComposerBusy(false);
      }
      return;
    }

    if (currentMode === "generate") {
      if (!pendingFiles.length && !message) {
        setStatus("Paste a job description or upload a posting to generate a draft.", "error");
        return;
      }
      setComposerBusy(true);
      try {
        const fileTexts = await readFilesAsText(pendingFiles);
        let jobDescription = message;
        if (fileTexts.length) {
          const combinedFileText = fileTexts
            .map((entry) => `# Source: ${entry.name}\n${entry.text}`)
            .join("\n\n");
          jobDescription = jobDescription
            ? `${jobDescription.trim()}\n\n${combinedFileText}`
            : combinedFileText;
        }
        if (!jobDescription || !jobDescription.trim()) {
          setStatus("Uploaded content was empty. Try again with more detail.", "error");
          return;
        }
        const summaryMessage = buildGenerationSummary(pendingFiles, message);
        if (textInput) {
          textInput.value = "";
        }
        clearPendingFiles();
        await handleGenerationRequest(summaryMessage, jobDescription);
      } finally {
        setComposerBusy(false);
      }
    }
  });
}

appendTranscriptMessage("assistant", initialGreeting);
setMode(currentMode);
updateSelectedFilesList();
