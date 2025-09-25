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
    display: grid;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: 1rem;
    background: var(--surface-primary);
    border: 1px solid var(--border-subtle);
    box-shadow: var(--shadow-sm);
    color: var(--text-primary);
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
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 0.85rem;
    color: var(--text-subtle);
  }

  .role {
    font-weight: 600;
    color: var(--text-muted);
  }

  .content {
    font-size: 1rem;
    line-height: 1.6;
    color: inherit;
    word-break: break-word;
    position: relative;
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
    margin: 0;
    padding: 0.5rem 0 0;
    list-style: none;
    display: grid;
    gap: 0.25rem;
    font-size: 0.85rem;
    color: var(--text-muted);
  }

  .attachments li {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.35rem 0.5rem;
    border-radius: 0.5rem;
    background: var(--attachment-bg);
    border: 1px solid var(--border-subtle);
  }

  .attachments .meta {
    color: var(--attachment-meta);
  }

  .error {
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
