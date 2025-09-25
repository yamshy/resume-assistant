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
        <span class="label">{step.label}</span>
        <span class="state">{getStepStatus(step.id)}</span>
      </li>
    {/each}
  </ol>
</section>

<style>
  .workflow-status {
    background: linear-gradient(150deg, var(--surface-secondary), var(--surface-muted));
    border: 1px solid var(--border-soft);
    border-radius: 1.1rem;
    padding: clamp(1rem, 3vw, 1.4rem);
    box-shadow: inset 0 0 0 1px var(--border-subtle), var(--shadow-sm);
    display: grid;
    gap: 0.75rem;
    color: var(--text-primary);
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  h2 {
    margin: 0;
    font-size: 1.05rem;
  }

  .badge {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    background: var(--surface-primary);
    border: 1px solid var(--border-subtle);
    text-transform: capitalize;
  }

  .badge.complete {
    background: var(--success-soft);
    border-color: var(--success);
    color: var(--success);
  }

  .badge.failed {
    background: var(--danger-soft);
    border-color: var(--danger);
    color: var(--danger);
  }

  ol {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0.6rem;
  }

  li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0.75rem;
    border-radius: 0.75rem;
    background: var(--surface-primary);
    border: 1px solid var(--border-subtle);
    text-transform: capitalize;
    font-size: 0.95rem;
  }

  li.running {
    border-color: var(--accent-strong);
  }

  li.complete {
    border-color: var(--success);
    color: var(--success);
  }

  li.error {
    border-color: var(--danger);
    color: var(--danger);
  }

  .state {
    font-size: 0.82rem;
    color: var(--text-subtle);
    text-transform: none;
  }
</style>
