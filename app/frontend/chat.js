const API_URL = "/chat";

const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");

let conversationHistory = [];

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
    const response = await fetch(API_URL, {
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

if (chatForm) {
  chatForm.addEventListener("submit", sendMessage);
}

if (chatLog) {
  const welcomeMessage =
    "Hi! I'm your resume assistant. Share a job posting and your experience so I can suggest how to tailor your résumé.";
  appendMessage("assistant", welcomeMessage);
  conversationHistory.push({ role: "assistant", content: welcomeMessage });
}
