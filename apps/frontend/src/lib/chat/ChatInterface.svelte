<script lang="ts">
  import { onMount } from "svelte";
  import MessageList from "./MessageList.svelte";
  import MessageInput from "./MessageInput.svelte";
  import WorkflowStatus from "./WorkflowStatus.svelte";
  import ApprovalPanel from "./ApprovalPanel.svelte";
  import { chatStore } from "./stores";
  import type { SendMessageOptions } from "./types";
  import { API_URL } from "./config";

  const store = chatStore;

  onMount(() => {
    store.initialize();
  });

  function handleSubmit(event: CustomEvent<SendMessageOptions>) {
    store.sendMessage(event.detail);
  }

  function handleReset() {
    store.reset();
  }

  function handleDismissError() {
    store.clearError();
  }

  function handleApprove(event: CustomEvent<{ feedback?: string }>) {
    store.submitApproval(true, event.detail.feedback);
  }

  function handleReject(event: CustomEvent<{ feedback?: string }>) {
    store.submitApproval(false, event.detail.feedback);
  }

  function handleRetryConnection() {
    void store.checkConnection();
  }

  $: state = $store;
  $: isBusy = Boolean(state.workflowId) && state.workflowStatus !== "complete" && state.workflowStatus !== "failed";
  $: progressList = Object.values(state.progress ?? {}).sort((a, b) =>
    a.timestamp.localeCompare(b.timestamp),
  );
  $: connectionStatus = state.connectionStatus;
  $: isBackendConnected = connectionStatus === "connected";
  $: connectionLabel =
    connectionStatus === "connected"
      ? "Backend online"
      : connectionStatus === "error"
        ? "Backend unreachable"
        : "Checking backend...";
  $: inputPlaceholder = isBackendConnected
    ? "Describe the updates you need..."
    : connectionStatus === "error"
      ? "Waiting for the backend to come back online..."
      : "Checking backend health...";
</script>

<section class="chat-interface" aria-live="polite">
  <header class="chat-header">
    <div>
      <h1>Resume Assistant</h1>
      <p class="subtitle">
        <span class="connection-group">
          <span
            class={`connection-status connection-${connectionStatus}`}
            role="status"
            aria-live="polite"
          >
            <span class="status-dot" aria-hidden="true"></span>
            {connectionLabel}
          </span>
          {#if connectionStatus === "error"}
            <button type="button" class="retry-connection" on:click={handleRetryConnection}>
              Retry connection
            </button>
          {/if}
        </span>
        <span class="separator" aria-hidden="true">·</span>
        Endpoint <code>{API_URL}</code>
        {#if state.workflowId}
          <span class="separator" aria-hidden="true">·</span>
          Workflow <span class="workflow-id">{state.workflowId}</span>
        {/if}
      </p>
    </div>
    <div class="header-actions">
      <button type="button" on:click={handleReset} disabled={isBusy}>
        New resume request
      </button>
    </div>
  </header>

  {#if state.error}
    <div class="error-banner" role="alert">
      <div class="error-content">
        <span class="error-message">{state.error}</span>
      </div>
      <button type="button" on:click={handleDismissError} aria-label="Dismiss error">×</button>
    </div>
  {/if}

  <MessageList messages={state.messages} isBusy={isBusy || state.isSubmitting || state.isPolling} progress={state.progress} />

  {#if state.awaitingApproval}
    <ApprovalPanel
      draft={state.draftPreview}
      busy={state.isPolling}
      error={state.approvalError}
      on:approve={handleApprove}
      on:reject={handleReject}
    />
  {/if}

  <footer class="chat-footer">
    <MessageInput
      on:submit={handleSubmit}
      disabled={isBusy || state.isSubmitting || !isBackendConnected}
      pending={state.isSubmitting}
      placeholder={inputPlaceholder}
    />
    {#if progressList.length > 0}
      <WorkflowStatus status={state.workflowStatus} progress={state.progress} awaitingApproval={state.awaitingApproval} />
    {/if}
  </footer>
</section>

<style>
  :global(body) {
    color: var(--text-primary);
    font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg-gradient);
    transition: background 400ms ease;
  }

  .chat-interface {
    display: grid;
    grid-template-rows: auto auto 1fr auto;
    gap: clamp(1rem, 2vw, 1.5rem);
    min-height: min(60rem, max(28rem, calc(100vh - 3rem)));
    width: min(64rem, calc(100% - 2.5rem));
    margin: clamp(1.5rem, 6vw, 3.5rem) auto;
    padding: clamp(1.5rem, 4vw, 3rem);
    box-sizing: border-box;
    border-radius: 1.75rem;
    border: 1px solid var(--border-strong);
    background: linear-gradient(155deg, var(--surface-primary), var(--surface-secondary));
    backdrop-filter: blur(26px);
    box-shadow: var(--shadow-lg);
    color: inherit;
  }

  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
  }

  .chat-header h1 {
    margin: 0;
    font-size: clamp(1.7rem, 3.4vw, 2.4rem);
    font-weight: 600;
    font-family: var(--heading-font);
    letter-spacing: 0.01em;
    color: var(--text-primary);
    text-shadow: 0 24px 50px rgba(0, 0, 0, 0.12);
  }

  .subtitle {
    margin: 0.35rem 0 0;
    font-size: 0.95rem;
    color: var(--text-subtle);
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    align-items: baseline;
  }

  .subtitle .separator {
    color: var(--text-subtle);
  }

  .subtitle code {
    font-family: "JetBrains Mono", monospace;
    font-size: 0.9rem;
    padding: 0.1rem 0.35rem;
    border-radius: 0.4rem;
    background: var(--surface-muted);
    border: 1px solid var(--border-subtle);
  }

  .connection-group {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }

  .retry-connection {
    border: none;
    background: transparent;
    color: var(--accent-strong);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    text-decoration: underline;
    text-decoration-thickness: 0.08em;
    text-underline-offset: 0.25rem;
    padding: 0.1rem 0.2rem;
  }

  .retry-connection:hover {
    color: var(--accent);
  }

  .retry-connection:focus-visible {
    outline: 2px solid var(--focus-ring);
    outline-offset: 2px;
    border-radius: 0.4rem;
  }

  .connection-status {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.15rem 0.65rem;
    border-radius: 9999px;
    border: 1px solid var(--border-subtle);
    background: var(--surface-pill);
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.01em;
  }

  .connection-status .status-dot {
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 9999px;
    background: var(--text-subtle);
    box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.04);
  }

  .connection-status.connection-connected {
    color: var(--success);
    border-color: rgba(60, 127, 101, 0.35);
  }

  .connection-status.connection-connected .status-dot {
    background: var(--success);
  }

  .connection-status.connection-error {
    color: var(--danger);
    border-color: rgba(200, 102, 87, 0.4);
  }

  .connection-status.connection-error .status-dot {
    background: var(--danger);
  }

  .connection-status.connection-idle {
    color: var(--warning);
    border-color: rgba(217, 145, 60, 0.35);
  }

  .connection-status.connection-idle .status-dot {
    background: var(--warning);
  }

  .workflow-id {
    font-family: "JetBrains Mono", monospace;
    background: var(--surface-muted);
    padding: 0.15rem 0.35rem;
    border-radius: 0.4rem;
    border: 1px solid var(--border-subtle);
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .header-actions button {
    border-radius: 9999px;
    padding: 0.6rem 1.3rem;
    font-weight: 600;
  }

  .error-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    border-radius: 1rem;
    background: var(--danger-soft);
    border: 1px solid var(--danger);
    color: var(--danger);
  }

  .error-content {
    display: grid;
    gap: 0.35rem;
  }

  .error-banner button {
    border: none;
    background: transparent;
    color: inherit;
    font-size: 1.2rem;
    cursor: pointer;
  }

  .chat-footer {
    display: grid;
    gap: clamp(1rem, 2vw, 1.5rem);
  }

  @media (min-width: 960px) {
    .chat-footer {
      grid-template-columns: minmax(0, 1fr) minmax(16rem, 20rem);
      align-items: start;
    }
  }
</style>
