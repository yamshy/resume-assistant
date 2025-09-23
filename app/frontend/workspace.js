const transcript = document.getElementById("chat-transcript");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const resumeUploadInput = document.getElementById("resume-upload");
const uploadButton = document.getElementById("upload-resumes");
const statusMessage = document.getElementById("status-message");
const sendButton = chatForm?.querySelector("button[type='submit']") ?? null;
const composerHint = chatForm?.querySelector(".composer-hint") ?? null;

const knowledgeUploadFallbackMessage =
  "Something went wrong while ingesting resumes. Double-check the files and try again.";
const missingOpenAIKeyNote = "Set the OPENAI_API_KEY environment variable to enable resume ingestion.";

let uploadConfigurationNote = null;

const initialGreeting =
  "Welcome! Upload a few of your past resumes so I can build a knowledge base, then paste a job description to create a tailored draft.";

const conversationHistory = [{ role: "assistant", content: initialGreeting }];
let sessionState = null;
let lastProfileDigest = null;

function appendTranscriptMessage(role, text, options = {}) {
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
  if (!chatForm) {
    return;
  }
  if (!uploadConfigurationNote) {
    uploadConfigurationNote = document.createElement("p");
    uploadConfigurationNote.className = "upload-configuration-note";
    if (composerHint) {
      chatForm.insertBefore(uploadConfigurationNote, composerHint);
    } else {
      chatForm.appendChild(uploadConfigurationNote);
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
  if (!profile) {
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

async function handleKnowledgeUpload(files) {
  if (!files.length) {
    return;
  }

  const summaryMessage = files.length === 1
    ? `Uploaded ${files[0].name} for ingestion.`
    : `Uploaded ${files.length} resumes: ${files.map((file) => file.name).join(", ")}.`;
  appendTranscriptMessage("user", summaryMessage);

  const formData = new FormData();
  files.forEach((file) => {
    formData.append("resumes", file, file.name);
  });

  if (uploadButton) {
    uploadButton.disabled = true;
  }
  if (sendButton) {
    sendButton.disabled = true;
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
  } finally {
    if (uploadButton) {
      uploadButton.disabled = false;
    }
    if (sendButton) {
      sendButton.disabled = false;
    }
    if (resumeUploadInput) {
      resumeUploadInput.value = "";
    }
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const rawMessage = chatInput.value;
  const message = rawMessage.trim();
  if (!message) {
    return;
  }

  chatInput.value = "";
  chatInput.focus();

  if (sendButton) {
    sendButton.disabled = true;
  }

  try {
    if (message.toLowerCase().startsWith("/generate")) {
      const description = message.replace(/^\/generate\s*/i, "").trim();
      if (!description) {
        appendTranscriptMessage(
          "system",
          "Include the job description after /generate so I know what to tailor.",
        );
        setStatus("Add a job description after /generate.", "error");
      } else {
        await handleGenerationRequest(message, description);
      }
    } else {
      await handleChatMessage(message);
    }
  } finally {
    if (sendButton) {
      sendButton.disabled = false;
    }
  }
});

if (uploadButton && resumeUploadInput) {
  uploadButton.addEventListener("click", () => {
    resumeUploadInput.click();
  });

  resumeUploadInput.addEventListener("change", async () => {
    const files = Array.from(resumeUploadInput.files || []);
    await handleKnowledgeUpload(files);
  });
}
