<script lang="ts">
  import { afterUpdate, onMount } from "svelte";
  import type { ChatMessage, ProgressRecord } from "./types";
  import StreamingMessage from "./StreamingMessage.svelte";

  export let messages: ChatMessage[] = [];
  export let isBusy = false;
  export let progress: Record<string, ProgressRecord> = {};

  let container: HTMLDivElement | null = null;
  let shouldStickToBottom = true;

  const SCROLL_THRESHOLD = 96;

  function onScroll() {
    if (!container) return;
    const { scrollTop, scrollHeight, clientHeight } = container;
    shouldStickToBottom = scrollHeight - (scrollTop + clientHeight) < SCROLL_THRESHOLD;
  }

  function scrollToBottom(force = false) {
    if (!container) return;
    if (force || shouldStickToBottom) {
      container.scrollTop = container.scrollHeight;
    }
  }

  onMount(() => {
    scrollToBottom(true);
  });

  afterUpdate(() => {
    scrollToBottom();
  });

  $: progressItems = Object.values(progress).sort((a, b) => a.timestamp.localeCompare(b.timestamp));
</script>

<section class="message-list">
  <div class="messages" bind:this={container} on:scroll={onScroll}>
    {#if messages.length === 0}
      <div class="empty-state">
        <p>Ask the assistant for help refining your resume or preparing for your next interview.</p>
      </div>
    {:else}
      <ul>
        {#each messages as message (message.id)}
          <StreamingMessage {message} />
        {/each}
      </ul>
    {/if}
    {#if isBusy}
      <div class="typing-indicator" aria-live="polite">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    {/if}
  </div>

  {#if progressItems.length > 0}
    <details class="progress-log">
      <summary>Detailed workflow updates</summary>
      <ul>
        {#each progressItems as item (item.node + item.timestamp)}
          <li class={item.status}>
            <div>
              <span class="node">{item.node}</span>
              <span class="time">{new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
            </div>
            {#if item.data}
              <pre>{JSON.stringify(item.data, null, 2)}</pre>
            {/if}
          </li>
        {/each}
      </ul>
    </details>
  {/if}
</section>

<style>
  .message-list {
    display: grid;
    gap: clamp(0.85rem, 2vw, 1.25rem);
    grid-template-rows: 1fr auto;
    min-height: 0;
  }

  .messages {
    background: linear-gradient(150deg, var(--surface-secondary), var(--surface-muted));
    border: 1px solid var(--border-soft);
    border-radius: 1.25rem;
    padding: clamp(1rem, 2vw, 1.25rem);
    overflow-y: auto;
    backdrop-filter: blur(18px);
    box-shadow: inset 0 0 0 1px var(--border-subtle), var(--shadow-md);
  }

  .messages ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0.9rem;
  }

  .empty-state {
    display: grid;
    place-items: center;
    min-height: 8rem;
    color: var(--text-muted);
    text-align: center;
    padding: 1rem;
  }

  .typing-indicator {
    display: inline-flex;
    gap: 0.4rem;
    padding: 0.55rem 0.85rem;
    border-radius: 9999px;
    background: var(--accent-soft);
    margin-top: 0.6rem;
    box-shadow: var(--shadow-sm);
  }

  .typing-indicator .dot {
    width: 0.45rem;
    height: 0.45rem;
    border-radius: 50%;
    background: var(--accent-strong);
    animation: pulse 1.2s infinite ease-in-out;
  }

  .typing-indicator .dot:nth-child(2) {
    animation-delay: 0.2s;
  }

  .typing-indicator .dot:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes pulse {
    0%,
    80%,
    100% {
      transform: scale(0.85);
      opacity: 0.45;
    }
    40% {
      transform: scale(1.05);
      opacity: 1;
    }
  }

  .progress-log {
    background: linear-gradient(155deg, var(--surface-elevated), var(--surface-secondary));
    border: 1px solid var(--border-soft);
    border-radius: 1rem;
    padding: 0.85rem 1rem;
    box-shadow: inset 0 0 0 1px var(--border-subtle);
    color: var(--text-primary);
  }

  .progress-log ul {
    list-style: none;
    margin: 0;
    padding: 0.75rem 0 0;
    display: grid;
    gap: 0.65rem;
  }

  .progress-log li {
    display: grid;
    gap: 0.35rem;
    padding: 0.6rem 0.75rem;
    border-radius: 0.75rem;
    background: var(--surface-primary);
    border: 1px solid var(--border-subtle);
  }

  .progress-log li.running {
    border-color: var(--accent-strong);
  }

  .progress-log li.complete {
    border-color: var(--success);
  }

  .progress-log li.error {
    border-color: var(--danger);
  }

  .progress-log .node {
    font-weight: 600;
    text-transform: capitalize;
  }

  .progress-log .time {
    color: var(--text-subtle);
    font-size: 0.85rem;
  }

  .progress-log pre {
    background: var(--surface-muted);
    border-radius: 0.5rem;
    padding: 0.5rem 0.75rem;
    margin: 0;
    font-size: 0.85rem;
    white-space: pre-wrap;
  }
</style>
