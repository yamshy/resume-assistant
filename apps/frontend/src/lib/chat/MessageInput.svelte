<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { formatFileSize } from "./utils";
  import type { SendMessageOptions } from "./types";

  const dispatch = createEventDispatcher<{ submit: SendMessageOptions }>();

  export let disabled = false;
  export let pending = false;
  export let placeholder = "Share the role, bullet points, or questions...";
  export let allowFileUpload = true;

  let content = "";
  let files: File[] = [];
  let fileInput: HTMLInputElement | null = null;

  function handleSubmit(event: Event) {
    event.preventDefault();
    const trimmed = content.trim();
    if (!trimmed && files.length === 0) {
      return;
    }

    dispatch("submit", { content, files });
    content = "";
    files = [];
    if (fileInput) {
      fileInput.value = "";
    }
  }

  function handleFileChange(event: Event) {
    const target = event.currentTarget as HTMLInputElement;
    files = Array.from(target.files ?? []);
  }

  function removeFile(index: number) {
    files = files.filter((_, fileIndex) => fileIndex !== index);
    if (files.length === 0 && fileInput) {
      fileInput.value = "";
    }
  }

</script>

<form class="message-input" on:submit={handleSubmit}>
  <label class="sr-only" for="chat-input">Send a message</label>
  <textarea
    id="chat-input"
    bind:value={content}
    rows={3}
    placeholder={placeholder}
    aria-label="Chat input"
    disabled={disabled}
  ></textarea>

  {#if allowFileUpload}
    <div class="file-upload">
      <label class="upload-button">
        <input
          type="file"
          multiple
          on:change={handleFileChange}
          disabled={disabled}
          bind:this={fileInput}
        />
        <span>Attach files</span>
      </label>
      {#if files.length > 0}
        <ul>
          {#each files as file, index (file.name + index)}
            <li>
              <span>{file.name}</span>
              <span class="meta">{formatFileSize(file.size)}</span>
              <button type="button" on:click={() => removeFile(index)} aria-label={`Remove ${file.name}`}>
                ×
              </button>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  {/if}

  <div class="actions">
    <button
      type="submit"
      disabled={disabled || (content.trim().length === 0 && files.length === 0)}
      class:pending
    >
      {#if pending}
        <span class="spinner" aria-hidden="true"></span>
        Sending
      {:else}
        Send message
      {/if}
    </button>
  </div>
</form>

<style>
  .message-input {
    display: grid;
    gap: 0.85rem;
    background: var(--surface-primary);
    border: 1px solid var(--border-strong);
    border-radius: 1.25rem;
    padding: clamp(1rem, 3vw, 1.35rem);
    box-shadow: var(--shadow-md);
  }

  textarea {
    width: 100%;
    resize: vertical;
    min-height: 5rem;
    border-radius: 1rem;
    border: 1px solid var(--border-subtle);
    background: var(--surface-secondary);
    color: var(--text-primary);
    padding: 0.85rem 1.1rem;
    font-size: 1rem;
    line-height: 1.55;
    box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.15);
    box-sizing: border-box;
    transition: border-color 150ms ease, box-shadow 150ms ease;
  }

  textarea:focus-visible {
    outline: 2px solid var(--focus-ring);
    outline-offset: 2px;
    border-color: var(--focus-ring);
    box-shadow: inset 0 0 0 1px var(--focus-ring);
  }

  textarea::placeholder {
    color: var(--text-subtle);
  }

  .file-upload {
    display: grid;
    gap: 0.6rem;
  }

  .upload-button {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    border-radius: 0.85rem;
    padding: 0.45rem 0.9rem;
    border: 1px dashed rgba(99, 102, 241, 0.35);
    background: rgba(99, 102, 241, 0.08);
    color: var(--accent-strong);
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: border-color 150ms ease, background 150ms ease;
  }

  .upload-button:hover {
    border-color: var(--accent-strong);
    background: rgba(99, 102, 241, 0.12);
  }

  .upload-button input {
    display: none;
  }

  .file-upload ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0.45rem;
  }

  .file-upload li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    padding: 0.45rem 0.6rem;
    border-radius: 0.75rem;
    background: var(--surface-secondary);
    font-size: 0.88rem;
    border: 1px solid var(--border-subtle);
    color: var(--text-primary);
  }

  .file-upload .meta {
    color: var(--text-subtle);
  }

  .file-upload button {
    border: none;
    background: transparent;
    color: var(--danger);
    font-size: 1.1rem;
    cursor: pointer;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
  }

  .actions button {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    border-radius: 0.9rem;
    border: none;
    padding: 0.6rem 1.4rem;
    background: linear-gradient(135deg, var(--accent), var(--accent-strong));
    color: var(--text-inverse);
    font-weight: 700;
    cursor: pointer;
    transition: transform 150ms ease, box-shadow 150ms ease;
    box-shadow: var(--shadow-md);
  }

  .actions button.pending {
    opacity: 0.85;
  }

  .actions button:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 28px 46px rgba(0, 0, 0, 0.18);
  }

  .actions button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
    box-shadow: none;
  }

  .spinner {
    width: 1rem;
    height: 1rem;
    border-radius: 50%;
    border: 2px solid rgba(255, 255, 255, 0.4);
    border-top-color: var(--text-inverse);
    animation: spin 1s linear infinite;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
