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

<section class="workspace" aria-live="polite">
  <aside class="overview" aria-label="Product introduction">
    <div class="overview-card">
      <span class="badge">Career Copilot</span>
      <h1>Reimagine your resume with guided AI support.</h1>
      <p>
        Describe the role you want, drop in past experience, and let the assistant orchestrate every step from
        draft to approval.
      </p>
    </div>

    <div class="pill-group">
      <div class="pill">
        <span>Targeted rewrites</span>
        <p>Share the role, industry, or job post and receive tailored copy instantly.</p>
      </div>
      <div class="pill">
        <span>Interview prep</span>
        <p>Surface quantified wins and suggested talking points from your draft.</p>
      </div>
      <div class="pill">
        <span>Human sign-off</span>
        <p>Review compliance, approve changes, and ship polished resumes in minutes.</p>
      </div>
    </div>

    <div class="meta">
      <h2>Connection</h2>
      <div class={`status-tile connection-${connectionStatus}`}>
        <span class="dot" aria-hidden="true"></span>
        <div>
          <strong>{connectionLabel}</strong>
          <small>Endpoint <code>{API_URL}</code></small>
        </div>
      </div>
      {#if state.workflowId}
        <div class="status-tile workflow">
          <span class="dot" aria-hidden="true"></span>
          <div>
            <strong>Workflow active</strong>
            <small>ID <span>{state.workflowId}</span></small>
          </div>
        </div>
      {/if}
    </div>
  </aside>

  <div class="conversation">
    <header class="chat-header">
      <div class="title-block">
        <h2>Live resume workspace</h2>
        <p>
          Keep the thread going to iterate on tone, achievements, and interview follow ups without leaving the chat.
        </p>
      </div>
      <div class="header-actions">
        {#if connectionStatus === "error"}
          <button type="button" class="ghost" on:click={handleRetryConnection}>Retry connection</button>
        {/if}
        <button type="button" on:click={handleReset} disabled={isBusy}>
          Start a new request
        </button>
      </div>
    </header>

    {#if state.error}
      <div class="error-banner" role="alert">
        <div class="error-content">
          <strong>Something went wrong.</strong>
          <span>{state.error}</span>
        </div>
        <button type="button" on:click={handleDismissError} aria-label="Dismiss error">Dismiss</button>
      </div>
    {/if}

    <MessageList
      messages={state.messages}
      isBusy={isBusy || state.isSubmitting || state.isPolling}
      progress={state.progress}
    />

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
        <WorkflowStatus
          status={state.workflowStatus}
          progress={state.progress}
          awaitingApproval={state.awaitingApproval}
        />
      {/if}
    </footer>
  </div>
</section>

<style>
  :global(body) {
    color: var(--text-primary);
    font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg-gradient);
    transition: background 400ms ease;
  }

  .workspace {
    display: grid;
    gap: clamp(1.5rem, 3vw, 2.5rem);
    grid-template-columns: minmax(0, 1fr);
    max-width: 1200px;
    margin: clamp(1.5rem, 6vw, 4rem) auto;
    padding: clamp(1.25rem, 4vw, 2rem);
    box-sizing: border-box;
  }

  .overview {
    display: grid;
    gap: clamp(1rem, 2vw, 1.4rem);
    background: var(--panel-gradient);
    border-radius: clamp(1.5rem, 2vw, 2rem);
    padding: clamp(1.5rem, 3vw, 2.2rem);
    border: 1px solid var(--panel-border);
    box-shadow: var(--panel-shadow);
    color: var(--panel-text);
  }

  .overview-card {
    display: grid;
    gap: 0.85rem;
  }

  .overview-card h1 {
    margin: 0;
    font-size: clamp(1.8rem, 3vw, 2.5rem);
    font-weight: 650;
    line-height: 1.2;
  }

  .overview-card p {
    margin: 0;
    color: var(--panel-text-muted);
    font-size: 1.05rem;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.12);
    color: inherit;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
  }

  .pill-group {
    display: grid;
    gap: 0.75rem;
  }

  .pill {
    display: grid;
    gap: 0.3rem;
    padding: 0.95rem 1.1rem;
    border-radius: 1rem;
    background: rgba(15, 23, 42, 0.25);
    border: 1px solid rgba(148, 163, 184, 0.2);
    color: inherit;
  }

  .pill span {
    font-weight: 600;
    font-size: 0.95rem;
  }

  .pill p {
    margin: 0;
    color: var(--panel-text-muted);
    font-size: 0.92rem;
    line-height: 1.4;
  }

  .meta {
    display: grid;
    gap: 0.75rem;
  }

  .meta h2 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  .status-tile {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.75rem;
    align-items: center;
    padding: 0.75rem 1rem;
    border-radius: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.25);
    background: rgba(15, 23, 42, 0.2);
    color: inherit;
  }

  .status-tile .dot {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 999px;
    background: var(--panel-indicator);
    box-shadow: 0 0 0 6px rgba(148, 163, 184, 0.16);
  }

  .status-tile strong {
    display: block;
    font-weight: 600;
    font-size: 0.95rem;
  }

  .status-tile small {
    color: var(--panel-text-subtle);
    font-size: 0.8rem;
    display: block;
  }

  .status-tile code {
    font-size: 0.8rem;
    padding: 0.1rem 0.3rem;
    border-radius: 0.4rem;
    background: rgba(15, 23, 42, 0.4);
  }

  .status-tile.workflow .dot {
    background: var(--accent);
    box-shadow: 0 0 0 6px rgba(99, 102, 241, 0.2);
  }

  .status-tile.connection-connected .dot {
    background: var(--success);
    box-shadow: 0 0 0 6px rgba(14, 197, 126, 0.2);
  }

  .status-tile.connection-error .dot {
    background: var(--danger);
    box-shadow: 0 0 0 6px rgba(239, 68, 68, 0.2);
  }

  .status-tile.connection-idle .dot {
    background: var(--warning);
    box-shadow: 0 0 0 6px rgba(250, 204, 21, 0.2);
  }

  .conversation {
    display: grid;
    gap: clamp(1rem, 2vw, 1.5rem);
    background: var(--surface-shell);
    border-radius: clamp(1.5rem, 2vw, 2rem);
    padding: clamp(1.3rem, 3vw, 2.2rem);
    border: 1px solid var(--border-strong);
    box-shadow: var(--shadow-lg);
  }

  .chat-header {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }

  .title-block h2 {
    margin: 0;
    font-size: clamp(1.4rem, 2.4vw, 1.9rem);
    font-weight: 600;
    letter-spacing: -0.01em;
  }

  .title-block p {
    margin: 0;
    color: var(--text-subtle);
    max-width: 38ch;
  }

  .header-actions {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
  }

  .header-actions button {
    border-radius: 9999px;
    padding: 0.55rem 1.3rem;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: transform 150ms ease, box-shadow 200ms ease, background 150ms ease;
  }

  .header-actions button:not(.ghost) {
    background: linear-gradient(135deg, var(--accent), var(--accent-strong));
    color: var(--text-inverse);
    box-shadow: 0 16px 35px rgba(79, 70, 229, 0.28);
  }

  .header-actions button:not(.ghost):hover:not(:disabled) {
    transform: translateY(-1px);
  }

  .header-actions button:not(.ghost):disabled {
    opacity: 0.5;
    cursor: not-allowed;
    box-shadow: none;
  }

  .header-actions .ghost {
    background: transparent;
    border: 1px solid var(--border-subtle);
    color: var(--text-muted);
  }

  .error-banner {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: center;
    background: var(--danger-soft);
    border: 1px solid var(--danger);
    color: var(--danger-strong);
    border-radius: 1rem;
    padding: 0.85rem 1.1rem;
  }

  .error-content {
    display: grid;
    gap: 0.15rem;
  }

  .error-content strong {
    font-size: 0.95rem;
  }

  .error-banner button {
    border: none;
    background: transparent;
    color: inherit;
    font-weight: 600;
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 0.25rem;
  }

  .chat-footer {
    display: grid;
    gap: clamp(1rem, 2vw, 1.5rem);
  }

  @media (min-width: 960px) {
    .workspace {
      grid-template-columns: minmax(18rem, 23rem) minmax(0, 1fr);
      align-items: start;
    }

    .chat-header {
      flex-direction: row;
      justify-content: space-between;
      align-items: center;
    }

    .title-block p {
      max-width: 32ch;
    }

    .chat-footer {
      grid-template-columns: minmax(0, 1fr) minmax(18rem, 22rem);
      align-items: start;
    }
  }
</style>
