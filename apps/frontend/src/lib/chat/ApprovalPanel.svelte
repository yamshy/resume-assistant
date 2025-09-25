<script lang="ts">
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher<{
    approve: { feedback?: string };
    reject: { feedback: string };
  }>();

  export let draft: unknown = null;
  export let busy = false;
  export let error: string | null = null;

  let feedback = "";

  $: previewText = typeof draft === "string"
    ? draft
    : draft && typeof draft === "object"
      ? JSON.stringify(draft, null, 2)
      : draft ?? "";

  function handleApprove() {
    dispatch("approve", { feedback: feedback.trim() || undefined });
    feedback = "";
  }

  function handleReject() {
    dispatch("reject", { feedback: feedback.trim() });
  }
</script>

<section class="approval" aria-live="polite">
  <header>
    <h2>Awaiting your approval</h2>
    <p>Review the draft below. Approve it or request changes with optional feedback.</p>
  </header>

  {#if previewText}
    <article>
      <pre>{previewText}</pre>
    </article>
  {/if}

  <label for="feedback">Feedback (optional)</label>
  <textarea
    id="feedback"
    bind:value={feedback}
    rows={4}
    placeholder="Share edits or notes for the assistant"
    disabled={busy}
  ></textarea>

  {#if error}
    <div class="error" role="alert">{error}</div>
  {/if}

  <div class="actions">
    <button type="button" class="secondary" on:click={handleReject} disabled={busy}>
      Request changes
    </button>
    <button type="button" on:click={handleApprove} disabled={busy}>
      Approve draft
    </button>
  </div>
</section>

<style>
  .approval {
    display: grid;
    gap: 0.85rem;
    background: linear-gradient(160deg, var(--surface-primary), var(--surface-secondary));
    border: 1px solid var(--border-soft);
    border-radius: 1.25rem;
    padding: clamp(1rem, 3vw, 1.5rem);
    box-shadow: inset 0 0 0 1px var(--border-subtle), var(--shadow-md);
    color: var(--text-primary);
  }

  header {
    display: grid;
    gap: 0.35rem;
  }

  header h2 {
    margin: 0;
    font-size: 1.15rem;
  }

  header p {
    margin: 0;
    color: var(--text-subtle);
    font-size: 0.95rem;
  }

  article {
    max-height: 18rem;
    overflow: auto;
    border-radius: 0.85rem;
    border: 1px solid var(--border-subtle);
    background: var(--surface-muted);
    padding: 0.75rem 1rem;
  }

  pre {
    margin: 0;
    white-space: pre-wrap;
    font-family: inherit;
    line-height: 1.55;
  }

  textarea {
    width: 100%;
    border-radius: 0.75rem;
    border: 1px solid var(--border-soft);
    background: var(--surface-primary);
    padding: 0.75rem 1rem;
    color: inherit;
    font-size: 1rem;
    resize: vertical;
    min-height: 6rem;
  }

  textarea:focus-visible {
    outline: 2px solid var(--focus-ring);
    outline-offset: 2px;
  }

  label {
    font-weight: 600;
  }

  .error {
    background: var(--danger-soft);
    color: var(--danger);
    border: 1px solid var(--danger);
    border-radius: 0.85rem;
    padding: 0.5rem 0.75rem;
    font-size: 0.9rem;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
  }

  button {
    border-radius: 9999px;
    padding: 0.6rem 1.4rem;
    font-weight: 600;
    cursor: pointer;
  }

  button.secondary {
    background: transparent;
    border: 1px solid var(--border-subtle);
    color: var(--text-primary);
  }

  button:not(.secondary) {
    background: var(--accent-strong);
    color: white;
    border: none;
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
