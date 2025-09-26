<script lang="ts">
  import { formatFileSize } from "./utils";
  import type { ChatMessage } from "./types";

  export let message: ChatMessage;

  const ROLE_LABELS: Record<ChatMessage["role"], string> = {
    user: "You",
    assistant: "Assistant",
    system: "System",
  };

  $: label = ROLE_LABELS[message.role] ?? "Unknown";
  $: textContent = message.content || (message.tokens ?? []).join("");
  $: isMultiline = textContent.includes("\n");
</script>

<li class={`message ${message.role} ${message.status}`}>
  <header>
    <span class="role">{label}</span>
    <time>{new Date(message.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>
  </header>
  <div class="content">
    {#if isMultiline}
      <pre>{textContent}</pre>
    {:else}
      <p>{textContent || '(empty)'}</p>
    {/if}
    {#if message.status === "pending"}
      <span class="cursor" aria-hidden="true">▋</span>
    {/if}
  </div>

  {#if message.attachments && message.attachments.length > 0}
    <ul class="attachments">
      {#each message.attachments as attachment (attachment.id)}
        <li>
          <span class="name">{attachment.name}</span>
          <span class="meta">{attachment.type || "unknown"} · {formatFileSize(attachment.size)}</span>
        </li>
      {/each}
    </ul>
  {/if}

  {#if message.error}
    <div class="error">{message.error}</div>
  {/if}
</li>

<style>
  .message {
    position: relative;
    display: grid;
    gap: 0.6rem;
    padding: 0.95rem 1.2rem;
    border-radius: 1rem;
    background: var(--surface-secondary);
    border: 1px solid var(--border-subtle);
    box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
    color: var(--text-primary);
    overflow: hidden;
  }

  .message::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: linear-gradient(120deg, rgba(99, 102, 241, 0.08), transparent 70%);
    pointer-events: none;
  }

  .message.user {
    background: var(--message-user-bg);
    border-color: var(--message-user-border);
  }

  .message.assistant {
    background: var(--message-assistant-bg);
    border-color: var(--message-assistant-border);
  }

  .message.system {
    background: var(--message-system-bg);
    border-color: var(--message-system-border);
  }

  header {
    position: relative;
    z-index: 1;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 0.85rem;
    color: var(--text-subtle);
  }

  .role {
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.75rem;
  }

  .content {
    position: relative;
    z-index: 1;
    font-size: 1rem;
    line-height: 1.6;
    color: inherit;
    word-break: break-word;
  }

  .content pre,
  .content p {
    margin: 0;
    white-space: pre-wrap;
  }

  .cursor {
    display: inline-block;
    margin-left: 0.1rem;
    color: var(--accent-strong);
    animation: blink 1s step-start infinite;
  }

  .attachments {
    position: relative;
    z-index: 1;
    margin: 0;
    padding: 0.5rem 0 0;
    list-style: none;
    display: grid;
    gap: 0.35rem;
    font-size: 0.85rem;
    color: var(--text-muted);
  }

  .attachments li {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.4rem 0.6rem;
    border-radius: 0.6rem;
    background: var(--attachment-bg);
    border: 1px solid var(--border-subtle);
  }

  .attachments .meta {
    color: var(--attachment-meta);
  }

  .error {
    position: relative;
    z-index: 1;
    color: var(--danger);
    background: var(--danger-soft);
    border: 1px solid var(--danger);
    border-radius: 0.75rem;
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
  }

  @keyframes blink {
    0%,
    50% {
      opacity: 1;
    }
    50.01%,
    100% {
      opacity: 0;
    }
  }
</style>
