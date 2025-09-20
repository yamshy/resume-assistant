const transcript = document.getElementById("chat-transcript");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const knowledgeForm = document.getElementById("knowledge-form");
const knowledgeFiles = document.getElementById("knowledge-files");
const knowledgeNotes = document.getElementById("knowledge-notes");
const generateForm = document.getElementById("generate-form");
const jobDescription = document.getElementById("job-description");
const statusMessage = document.getElementById("status-message");

const initialGreeting =
  "Welcome! Upload a few of your past resumes so I can build a knowledge base, then paste a job description to create a tailored draft.";

const conversationHistory = [{ role: "assistant", content: initialGreeting }];
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

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) {
    return;
  }

  appendTranscriptMessage("user", message);
  conversationHistory.push({ role: "user", content: message });
  chatInput.value = "";
  chatInput.focus();

  const submitButton = chatForm.querySelector("button[type='submit']");
  if (submitButton) {
    submitButton.disabled = true;
  }

  setStatus("Thinking through your request...", "pending");

  try {
    const payload = await postJSON("/chat", { messages: conversationHistory });
    const assistantMessage = payload?.message?.content || "I'm here to help.";
    appendTranscriptMessage("assistant", assistantMessage);
    conversationHistory.push({ role: "assistant", content: assistantMessage });

    if (payload?.follow_up) {
      appendTranscriptMessage("system", payload.follow_up);
    }

    maybeShowProfileSnapshot(payload?.profile_snapshot);
    setStatus("Conversation updated.", "success");
  } catch (error) {
    appendTranscriptMessage("system", "I couldn't reach the chat endpoint. Please try again.");
    setStatus(`Chat failed: ${error.message}`, "error");
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
    }
  }
});

knowledgeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!knowledgeFiles.files.length) {
    setStatus("Select at least one resume file to ingest.", "error");
    return;
  }

  const submitButton = knowledgeForm.querySelector("button[type='submit']");
  if (submitButton) {
    submitButton.disabled = true;
  }

  const formData = new FormData();
  Array.from(knowledgeFiles.files).forEach((file) => {
    formData.append("resumes", file, file.name);
  });
  const notes = knowledgeNotes.value.trim();
  if (notes) {
    formData.append("notes", notes);
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

    if (result.profile_snapshot) {
      const heading = document.createElement("h3");
      heading.textContent = "Profile snapshot";
      const snapshotPre = document.createElement("pre");
      snapshotPre.textContent = JSON.stringify(result.profile_snapshot, null, 2);
      detailCard.appendChild(heading);
      detailCard.appendChild(snapshotPre);
      lastProfileDigest = JSON.stringify(result.profile_snapshot);
    }

    appendTranscriptMessage("assistant", summaryParts.join(" "), { detailElement: detailCard });

    setStatus("Resumes ingested successfully.", "success");
    knowledgeForm.reset();
    knowledgeFiles.value = "";
  } catch (error) {
    appendTranscriptMessage(
      "system",
      "Something went wrong while ingesting resumes. Double-check the files and try again.",
    );
    setStatus(`Ingestion failed: ${error.message}`, "error");
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
    }
  }
});

generateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const description = jobDescription.value.trim();
  if (!description) {
    setStatus("Paste a job description to generate a resume.", "error");
    return;
  }

  const submitButton = generateForm.querySelector("button[type='submit']");
  if (submitButton) {
    submitButton.disabled = true;
  }

  setStatus("Generating a tailored resume...", "pending");

  try {
    const resume = await postJSON("/generate", { job_posting: description });
    const card = createResultCard("Generated resume", resume);
    appendTranscriptMessage(
      "assistant",
      "Here's a structured resume draft based on the job description.",
      { detailElement: card },
    );
    setStatus("Resume generated.", "success");
    generateForm.reset();
  } catch (error) {
    appendTranscriptMessage(
      "system",
      "I couldn't generate a resume. Upload resumes to the knowledge base or try again with more detail.",
    );
    setStatus(`Generation failed: ${error.message}`, "error");
  } finally {
    if (submitButton) {
      submitButton.disabled = false;
    }
  }
});
