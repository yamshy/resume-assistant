<script lang="ts">
  import type { ProgressRecord, WorkflowStatus } from "./types";

  export let status: WorkflowStatus = "idle";
  export let progress: Record<string, ProgressRecord> = {};
  export let awaitingApproval = false;

  const steps: { id: string; label: string }[] = [
    { id: "drafting", label: "Drafting" },
    { id: "reviewing", label: "Review" },
    { id: "awaiting_approval", label: "Approval" },
    { id: "compliance", label: "Compliance" },
    { id: "complete", label: "Complete" },
  ];

  function getStepStatus(id: string): ProgressRecord["status"] {
    const record = progress[id];
    if (!record) {
      return "pending";
    }
    return record.status;
  }

  function describe(statusValue: WorkflowStatus, awaiting: boolean): string {
    if (awaiting || statusValue === "awaiting_approval") {
      return "Waiting for your approval";
    }
    switch (statusValue) {
      case "drafting":
        return "Drafting in progress";
      case "reviewing":
        return "Under review";
      case "compliance":
        return "Compliance checks running";
      case "complete":
        return "Resume complete";
      case "failed":
        return "Workflow failed";
      default:
        return "Waiting to start";
    }
  }

  $: statusDescription = describe(status, awaitingApproval);
</script>

<section class="workflow-status" aria-live="polite">
  <header>
    <h2>Workflow status</h2>
    <span class={`badge ${status}`}>{statusDescription}</span>
  </header>
  <ol>
    {#each steps as step (step.id)}
      <li class={getStepStatus(step.id)}>
        <span class="marker" aria-hidden="true"></span>
        <div class="copy">
          <span class="label">{step.label}</span>
          <span class="state">{getStepStatus(step.id)}</span>
        </div>
      </li>
    {/each}
  </ol>
</section>

<style>
  .workflow-status {
    background: var(--surface-primary);
    border: 1px solid var(--border-strong);
    border-radius: 1.2rem;
    padding: clamp(1rem, 3vw, 1.4rem);
    box-shadow: var(--shadow-sm);
    display: grid;
    gap: 0.9rem;
    color: var(--text-primary);
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
  }

  h2 {
    margin: 0;
    font-size: 1.05rem;
  }

  .badge {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.3rem 0.65rem;
    border-radius: 9999px;
    background: var(--accent-soft);
    color: var(--accent-strong);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .badge.complete {
    background: var(--success-soft);
    color: var(--success);
  }

  .badge.failed {
    background: var(--danger-soft);
    color: var(--danger);
  }

  ol {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0.75rem;
  }

  li {
    position: relative;
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.8rem;
    align-items: center;
    padding: 0.6rem 0.75rem;
    border-radius: 0.9rem;
    background: var(--surface-secondary);
    border: 1px solid var(--border-subtle);
    text-transform: capitalize;
    font-size: 0.95rem;
  }

  li.running {
    border-color: var(--accent-strong);
    box-shadow: 0 12px 24px rgba(99, 102, 241, 0.15);
  }

  li.complete {
    border-color: var(--success);
    color: var(--success);
  }

  li.error {
    border-color: var(--danger);
    color: var(--danger);
  }

  .marker {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 50%;
    background: var(--border-subtle);
    box-shadow: 0 0 0 6px rgba(148, 163, 184, 0.16);
  }

  li.running .marker {
    background: var(--accent-strong);
    box-shadow: 0 0 0 6px rgba(99, 102, 241, 0.16);
  }

  li.complete .marker {
    background: var(--success);
    box-shadow: 0 0 0 6px rgba(14, 197, 126, 0.18);
  }

  li.error .marker {
    background: var(--danger);
    box-shadow: 0 0 0 6px rgba(239, 68, 68, 0.2);
  }

  .copy {
    display: grid;
    gap: 0.25rem;
  }

  .state {
    font-size: 0.78rem;
    color: var(--text-subtle);
    text-transform: none;
  }
</style>
