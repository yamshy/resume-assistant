const KNOWLEDGE_API_URL = "/knowledge";
const GENERATE_API_URL = "/generate";

const MODE_INGEST = "ingest";
const MODE_GENERATE = "generate";

const activityLog = document.getElementById("activity-log");
const workflowForm = document.getElementById("workflow-form");
const statusMessage = document.getElementById("status-message");

const modeButtons = document.querySelectorAll(".mode-button");
const composerSections = document.querySelectorAll(".composer-section");

const resumeFilesInput = document.getElementById("resume-files");
const ingestNotesInput = document.getElementById("ingest-notes");
const jobDescriptionInput = document.getElementById("job-description");

let activeMode = MODE_INGEST;

const KIND_LABELS = {
  info: "Update",
  success: "Success",
  error: "Error",
  note: "Next step",
};

function clearPlaceholder() {
  const placeholder = activityLog?.querySelector("[data-placeholder=true]");
  if (placeholder) {
    placeholder.remove();
  }
}

function appendActivity(kind, content) {
  if (!activityLog || !content) {
    return;
  }

  clearPlaceholder();

  const entry = document.createElement("section");
  entry.classList.add("activity-entry", `activity-entry--${kind}`);

  const label = document.createElement("span");
  label.classList.add("activity-entry__label");
  label.textContent = KIND_LABELS[kind] ?? "Update";

  const body = document.createElement("p");
  body.classList.add("activity-entry__content");
  body.textContent = content;

  entry.append(label, body);
  activityLog.append(entry);
  activityLog.scrollTo({ top: activityLog.scrollHeight, behavior: "smooth" });
}

function appendStructuredActivity(label, payload) {
  if (!activityLog) {
    return;
  }

  clearPlaceholder();

  const entry = document.createElement("section");
  entry.classList.add("activity-entry", "activity-entry--structured");

  const header = document.createElement("header");
  header.classList.add("activity-entry__header");

  const title = document.createElement("span");
  title.classList.add("activity-entry__label");
  title.textContent = label;

  header.append(title);
  entry.append(header);

  const body = document.createElement("pre");
  body.classList.add("activity-entry__structured");
  if (typeof payload === "string") {
    body.textContent = payload;
  } else {
    body.textContent = JSON.stringify(payload, null, 2);
  }

  entry.append(body);
  activityLog.append(entry);
  activityLog.scrollTo({ top: activityLog.scrollHeight, behavior: "smooth" });
}

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

    appendActivity("success", summary);

    const snapshot = data.profile_snapshot;
    if (snapshot && typeof snapshot === "object" && Object.keys(snapshot).length > 0) {
      appendStructuredActivity("Profile snapshot", snapshot);
    } else {
      appendStructuredActivity("Ingestion response", data);
    }

    if (Array.isArray(data.skills_indexed) && data.skills_indexed.length > 0) {
      const preview = data.skills_indexed.slice(0, 5).join(", ");
      appendActivity("info", `New skills captured: ${preview}${data.skills_indexed.length > 5 ? "…" : ""}`);
    }

    appendActivity(
      "note",
      "Validate the extracted details above before proceeding to resume generation.",
    );

    setStatus("Resumes ingested successfully.", "success");

    if (resumeFilesInput) {
      resumeFilesInput.value = "";
    }
    if (ingestNotesInput) {
      ingestNotesInput.value = "";
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to ingest resumes.";
    setStatus(message, "error");
    appendActivity("error", message);
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
    appendActivity("success", "Resume generated successfully.");
    appendStructuredActivity("Generated resume", data);
    appendActivity(
      "note",
      "Review the generated resume above and capture any human-in-the-loop adjustments before delivery.",
    );

    setStatus("Resume generated successfully.", "success");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to generate resume.";
    setStatus(message, "error");
    appendActivity("error", message);
  }
}

function handleSubmit(event) {
  event.preventDefault();

  if (activeMode === MODE_INGEST) {
    processIngestion();
  } else if (activeMode === MODE_GENERATE) {
    processGeneration();
  }
}

if (workflowForm) {
  workflowForm.addEventListener("submit", handleSubmit);
}

if (modeButtons.length) {
  modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const mode = button.dataset.mode;
      if (mode && mode !== activeMode) {
        setMode(mode);

        if (mode === MODE_INGEST && resumeFilesInput) {
          resumeFilesInput.focus();
        } else if (mode === MODE_GENERATE && jobDescriptionInput) {
          jobDescriptionInput.focus();
        }
      }
    });
  });
}

if (activityLog) {
  appendActivity(
    "info",
    "Upload one or more resumes to build your structured skills and experience database, then switch to Generate to tailor a draft for a job posting.",
  );
}

setMode(activeMode);
