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
    <div>
      <h2>Awaiting your approval</h2>
      <p>Review the generated draft, leave feedback, and choose whether to move forward.</p>
    </div>
    <span class="badge">Step 3 · Approval</span>
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
    <button type="button" class="ghost" on:click={handleReject} disabled={busy}>
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
    background: var(--surface-primary);
    border: 1px solid var(--border-strong);
    border-radius: 1.25rem;
    padding: clamp(1rem, 3vw, 1.5rem);
    box-shadow: var(--shadow-md);
    color: var(--text-primary);
  }

  header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
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

  header .badge {
    align-self: flex-end;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.8rem;
    border-radius: 999px;
    background: var(--accent-soft);
    color: var(--accent-strong);
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  article {
    max-height: 18rem;
    overflow: auto;
    border-radius: 0.85rem;
    border: 1px solid var(--border-subtle);
    background: var(--surface-secondary);
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
    border: 1px solid var(--border-subtle);
    background: var(--surface-secondary);
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
    border-radius: 0.9rem;
    padding: 0.6rem 1.4rem;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: transform 150ms ease, box-shadow 150ms ease;
  }

  button.ghost {
    background: transparent;
    border: 1px solid var(--border-subtle);
    color: var(--text-muted);
  }

  button:not(.ghost) {
    background: linear-gradient(135deg, var(--accent), var(--accent-strong));
    color: var(--text-inverse);
    box-shadow: 0 18px 36px rgba(99, 102, 241, 0.24);
  }

  button:not(.ghost):hover:not(:disabled) {
    transform: translateY(-1px);
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    box-shadow: none;
  }
</style>
