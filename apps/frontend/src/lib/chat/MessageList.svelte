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
        <h3>Your AI workspace is ready</h3>
        <p>Share the role, paste bullet points, or upload supporting files to get a focused rewrite.</p>
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
      <summary>Workflow activity log</summary>
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
    position: relative;
    background: var(--surface-primary);
    border: 1px solid var(--border-strong);
    border-radius: 1.25rem;
    padding: clamp(1rem, 2vw, 1.25rem);
    overflow-y: auto;
    box-shadow: var(--shadow-md);
  }

  .messages::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), transparent 70%);
    pointer-events: none;
  }

  .messages ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 1rem;
    position: relative;
    z-index: 1;
  }

  .empty-state {
    position: relative;
    z-index: 1;
    display: grid;
    gap: 0.5rem;
    place-items: center;
    min-height: 8rem;
    text-align: center;
    padding: 1.5rem;
    color: var(--text-muted);
  }

  .empty-state h3 {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 600;
  }

  .empty-state p {
    margin: 0;
    max-width: 32ch;
    color: var(--text-subtle);
  }

  .typing-indicator {
    position: relative;
    z-index: 1;
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.55rem 0.95rem;
    border-radius: 9999px;
    background: var(--accent-soft);
    margin-top: 0.75rem;
    box-shadow: var(--shadow-sm);
  }

  .typing-indicator .dot {
    width: 0.4rem;
    height: 0.4rem;
    border-radius: 50%;
    background: var(--accent-strong);
    animation: pulse 1.2s infinite ease-in-out;
  }

  .typing-indicator .dot:nth-child(2) {
    animation-delay: 0.18s;
  }

  .typing-indicator .dot:nth-child(3) {
    animation-delay: 0.36s;
  }

  @keyframes pulse {
    0%,
    80%,
    100% {
      transform: scale(0.85);
      opacity: 0.4;
    }
    40% {
      transform: scale(1);
      opacity: 1;
    }
  }

  .progress-log {
    background: var(--surface-secondary);
    border: 1px solid var(--border-strong);
    border-radius: 1rem;
    padding: 0.85rem 1rem;
    box-shadow: var(--shadow-sm);
    color: var(--text-primary);
  }

  .progress-log summary {
    cursor: pointer;
    font-weight: 600;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 0.4rem;
    position: relative;
  }

  .progress-log summary::after {
    content: "";
    width: 0.6rem;
    height: 0.6rem;
    border-right: 2px solid currentColor;
    border-bottom: 2px solid currentColor;
    transform: rotate(-45deg);
    transition: transform 150ms ease;
  }

  .progress-log[open] summary::after {
    transform: rotate(45deg);
  }

  .progress-log summary::-webkit-details-marker {
    display: none;
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
    border-radius: 0.85rem;
    background: var(--surface-primary);
    border: 1px solid var(--border-subtle);
    transition: border-color 150ms ease, box-shadow 150ms ease;
  }

  .progress-log li.running {
    border-color: var(--accent-strong);
    box-shadow: 0 10px 20px rgba(99, 102, 241, 0.12);
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
    border-radius: 0.6rem;
    padding: 0.5rem 0.75rem;
    margin: 0;
    font-size: 0.85rem;
    white-space: pre-wrap;
  }
</style>
