const CHAT_API_URL = "/chat";
const KNOWLEDGE_API_URL = "/knowledge";
const GENERATE_API_URL = "/generate";

const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");

const knowledgeForm = document.getElementById("knowledge-form");
const knowledgeContentInput = document.getElementById("knowledge-content");
const knowledgeMetadataInput = document.getElementById("knowledge-metadata");
const knowledgeStatus = document.getElementById("knowledge-status");

const generateForm = document.getElementById("generate-form");
const jobPostingInput = document.getElementById("job-posting");
const profileJsonInput = document.getElementById("profile-json");
const generateStatus = document.getElementById("generate-status");
const generateResult = document.getElementById("generate-result");

let conversationHistory = [];

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

async function sendMessage(event) {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  const payloadHistory = [...conversationHistory];
  appendMessage("user", message);
  messageInput.value = "";

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
    appendMessage("system", error.message || "Unknown error");
  }
}

async function ingestKnowledge(event) {
  event.preventDefault();
  const content = knowledgeContentInput?.value.trim();
  const metadataRaw = knowledgeMetadataInput?.value.trim();

  if (!content) {
    setStatus(knowledgeStatus, "Document content is required.", "error");
    return;
  }

  let metadata = {};
  if (metadataRaw) {
    try {
      metadata = JSON.parse(metadataRaw);
    } catch (error) {
      setStatus(knowledgeStatus, "Metadata must be valid JSON.", "error");
      return;
    }
  }

  setStatus(knowledgeStatus, "Ingesting document...");

  try {
    const response = await fetch(KNOWLEDGE_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        documents: [
          {
            content,
            metadata,
          },
        ],
      }),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    const ingested = typeof data.ingested === "number" ? data.ingested : 0;
    setStatus(knowledgeStatus, `Stored ${ingested} document${ingested === 1 ? "" : "s"} in the knowledge base.`, "success");

    if (knowledgeContentInput) {
      knowledgeContentInput.value = "";
    }
    if (knowledgeMetadataInput) {
      knowledgeMetadataInput.value = "";
    }
  } catch (error) {
    setStatus(knowledgeStatus, error.message || "Unable to ingest document.", "error");
  }
}

async function generateResume(event) {
  event.preventDefault();
  const jobPosting = jobPostingInput?.value.trim();
  const profileRaw = profileJsonInput?.value.trim();

  if (!jobPosting || !profileRaw) {
    setStatus(generateStatus, "Job posting and profile are required.", "error");
    return;
  }

  let profile;
  try {
    profile = JSON.parse(profileRaw);
  } catch (error) {
    setStatus(generateStatus, "Profile must be valid JSON.", "error");
    return;
  }

  setStatus(generateStatus, "Generating resume...");
  if (generateResult) {
    generateResult.textContent = "";
  }

  try {
    const response = await fetch(GENERATE_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        job_posting: jobPosting,
        profile,
      }),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    setStatus(generateStatus, "Resume generated successfully.", "success");

    if (generateResult) {
      generateResult.textContent = JSON.stringify(data, null, 2);
    }
  } catch (error) {
    setStatus(generateStatus, error.message || "Unable to generate resume.", "error");
  }
}

if (chatForm) {
  chatForm.addEventListener("submit", sendMessage);
}

if (knowledgeForm) {
  knowledgeForm.addEventListener("submit", ingestKnowledge);
}

if (generateForm) {
  generateForm.addEventListener("submit", generateResume);
}

if (chatLog) {
  const welcomeMessage =
    "Hi! I'm your resume assistant. Share a job posting and your experience so I can suggest how to tailor your résumé.";
  appendMessage("assistant", welcomeMessage);
  conversationHistory.push({ role: "assistant", content: welcomeMessage });
}
