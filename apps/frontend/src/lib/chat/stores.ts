import { get, writable } from "svelte/store";
import {
  getHealth,
  getResult,
  getStatus,
  startWorkflow,
  submitApproval,
} from "../api/resume";
import { WORKFLOW_STORAGE_KEY } from "./config";
import type {
  AttachmentPayload,
  ChatMessage,
  ChatState,
  ProgressRecord,
  SendMessageOptions,
  StartWorkflowPayload,
  WorkflowStatus,
  ResumeWorkflowState,
} from "./types";
import {
  buildAttachmentPayload,
  createId,
  nowIso,
  stripMarkdown,
  toBase64,
} from "./utils";

const WORKFLOW_STEPS = ["drafting", "reviewing", "compliance", "complete"] as const;
type WorkflowStep = (typeof WORKFLOW_STEPS)[number];

const POLL_INTERVAL_MS = 3500;

function normalizeWorkflowStatus(state: ResumeWorkflowState | null | undefined): WorkflowStatus {
  if (!state) return "unknown";

  const stage = state.stage?.toLowerCase();
  const status = state.status?.toLowerCase();

  if (status === "error") {
    return "failed";
  }

  if (stage === "done" || status === "complete") {
    return "complete";
  }

  if (stage === "revision" && status !== "complete") {
    return "awaiting_approval";
  }

  if (stage === "compliance") {
    return "compliance";
  }

  if (stage === "critique" || stage === "publishing") {
    return "reviewing";
  }

  if (stage === "drafting" || stage === "ingestion" || stage === "route") {
    return "drafting";
  }

  if (status === "pending" || status === "in_progress") {
    return "drafting";
  }

  return "unknown";
}

function toRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function unwrapContent(value: unknown): unknown {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return value;
  }
  const record = value as Record<string, unknown>;
  if (typeof record.content === "string") {
    return record.content;
  }
  if (typeof record.text === "string") {
    return record.text;
  }
  return value;
}

function pickArtifactValue(artifacts: Record<string, unknown> | null, keys: string[]): unknown {
  if (!artifacts) return undefined;
  for (const key of keys) {
    if (key in artifacts) {
      const raw = artifacts[key];
      if (raw !== undefined && raw !== null && raw !== "") {
        return unwrapContent(raw);
      }
    }
  }
  return undefined;
}

function getRecordValue(record: Record<string, unknown> | null, key: string): unknown {
  if (!record || !(key in record)) {
    return undefined;
  }
  return record[key];
}

function extractDraftFromState(state: ResumeWorkflowState | null | undefined): unknown {
  if (!state) return undefined;
  const artifacts = toRecord(state.artifacts ?? null);
  const draftKeys = ["draft", "draft_resume", "resume_draft", "latest_draft", "current_draft"];
  const direct = pickArtifactValue(artifacts, draftKeys);
  if (direct !== undefined) {
    return direct;
  }

  const drafts = getRecordValue(artifacts, "drafts");
  if (Array.isArray(drafts) && drafts.length > 0) {
    return unwrapContent(drafts[drafts.length - 1]);
  }

  const messages = state.messages;
  if (Array.isArray(messages)) {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const message = messages[index];
      if (message?.role === "assistant" && message.content) {
        return message.content;
      }
    }
  }

  return undefined;
}

function extractResultFromState(state: ResumeWorkflowState | null | undefined): unknown {
  if (!state) return undefined;
  const artifacts = toRecord(state.artifacts ?? null);
  const resultKeys = [
    "final_resume",
    "resume",
    "result",
    "output",
    "final_result",
    "finalResume",
  ];
  const direct = pickArtifactValue(artifacts, resultKeys);
  if (direct !== undefined) {
    return direct;
  }

  const draft = extractDraftFromState(state);
  if (draft !== undefined) {
    return draft;
  }

  const messages = state.messages;
  if (Array.isArray(messages)) {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const message = messages[index];
      if (message?.role === "assistant" && message.content) {
        return message.content;
      }
    }
  }

  if (artifacts) {
    return artifacts;
  }

  return state;
}

function isAwaitingApprovalState(state: ResumeWorkflowState | null | undefined): boolean {
  if (!state) return false;
  if (state.stage === "revision" && state.status !== "complete") {
    return true;
  }

  const artifacts = toRecord(state.artifacts ?? null);
  const flags = toRecord(state.flags ?? null);

  const candidateKeys = [
    "awaitingApproval",
    "awaiting_approval",
    "approvalNeeded",
    "requiresApproval",
    "awaitingHuman",
    "awaiting_human",
  ];

  const candidates = candidateKeys
    .map((key) => getRecordValue(artifacts, key))
    .concat(candidateKeys.map((key) => getRecordValue(flags, key)));

  for (const candidate of candidates) {
    if (typeof candidate === "boolean") {
      return candidate;
    }
  }

  return false;
}

function statusToStep(status: WorkflowStatus): WorkflowStep | null {
  if (status === "awaiting_approval") {
    return "reviewing";
  }
  if (WORKFLOW_STEPS.includes(status as WorkflowStep)) {
    return status as WorkflowStep;
  }
  if (status === "failed" || status === "unknown") {
    return null;
  }
  return null;
}

function describeStatus(status: WorkflowStatus, awaitingApproval: boolean): string {
  if (awaitingApproval || status === "awaiting_approval") {
    return "A draft is ready for your approval.";
  }
  switch (status) {
    case "drafting":
      return "The assistant is drafting your resume.";
    case "reviewing":
      return "Reviewing the draft for quality.";
    case "compliance":
      return "Running compliance checks.";
    case "complete":
      return "Your resume is ready.";
    case "failed":
      return "The workflow encountered an error.";
    default:
      return "Working on your resume.";
  }
}

function computeProgress(
  existing: Record<string, ProgressRecord>,
  status: WorkflowStatus,
  awaitingApproval: boolean,
): Record<string, ProgressRecord> {
  const now = nowIso();
  const currentStep = statusToStep(status);
  const currentIndex = currentStep ? WORKFLOW_STEPS.indexOf(currentStep) : -1;
  const next: Record<string, ProgressRecord> = {};

  for (const [index, step] of WORKFLOW_STEPS.entries()) {
    const previous = existing[step];
    let stepStatus: ProgressRecord["status"] = "pending";
    if (status === "failed" && (!currentStep || currentStep === step)) {
      stepStatus = "error";
    } else if (currentIndex === -1) {
      stepStatus = index === 0 ? "running" : "pending";
    } else if (index < currentIndex) {
      stepStatus = "complete";
    } else if (index === currentIndex) {
      stepStatus = status === "complete" ? "complete" : "running";
    } else {
      stepStatus = "pending";
    }

    const hasChanged = !previous || previous.status !== stepStatus;
    next[step] = {
      node: step,
      status: stepStatus,
      data: { status },
      timestamp: hasChanged ? now : previous?.timestamp ?? now,
    };
  }

  const prevAwaiting = existing.awaiting_approval;
  if (awaitingApproval) {
    next.awaiting_approval = {
      node: "awaiting_approval",
      status: "running",
      data: { status: "awaiting_approval" },
      timestamp: prevAwaiting && prevAwaiting.status === "running" ? prevAwaiting.timestamp : now,
    };
  } else if (prevAwaiting) {
    next.awaiting_approval = {
      node: "awaiting_approval",
      status: prevAwaiting.status === "complete" ? "complete" : "complete",
      data: { status: "resolved" },
      timestamp: now,
    };
  }

  return next;
}

function formatError(error: unknown): string {
  if (typeof Response !== "undefined" && error instanceof Response) {
    return `HTTP ${error.status} ${error.statusText}`.trim();
  }
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  if (error && typeof error === "object" && "message" in error) {
    const message = (error as { message?: unknown }).message;
    if (typeof message === "string") {
      return message;
    }
  }
  try {
    return JSON.stringify(error);
  } catch {
    return "Unexpected error";
  }
}

async function encodeAttachments(files?: File[]): Promise<AttachmentPayload[]> {
  if (!files || files.length === 0) {
    return [];
  }

  const encoded: AttachmentPayload[] = [];
  for (const file of files) {
    try {
      const buffer = await file.arrayBuffer();
      const base64 = toBase64(buffer);
      encoded.push(buildAttachmentPayload(file, base64));
    } catch (error) {
      console.warn("Failed to encode attachment", error);
    }
  }
  return encoded;
}

async function preparePayload(options: SendMessageOptions): Promise<{
  messagePayload: StartWorkflowPayload;
  userMessage: ChatMessage | null;
}> {
  const content = options.content?.trim() ?? "";
  const files = options.files ?? [];
  const attachments = await encodeAttachments(files);
  const timestamp = nowIso();
  const userMessage = content.length > 0 || attachments.length > 0
    ? {
        id: createId("user"),
        role: "user" as const,
        content,
        tokens: content ? [content] : [],
        status: "complete" as const,
        createdAt: timestamp,
        metadata: options.metadata,
        attachments: attachments.length > 0
          ? attachments.map((attachment) => {
              const { data, ...rest } = attachment;
              void data;
              return rest;
            })
          : undefined,
        error: null,
      }
    : null;

  const artifacts: Record<string, unknown> = {};
  if (content.length > 0 || attachments.length > 0) {
    artifacts.messages = [
      {
        role: "human",
        content,
        model: null,
      },
    ];
  }

  if (attachments.length > 0) {
    artifacts.attachments = attachments;
  }

  if (options.metadata && Object.keys(options.metadata).length > 0) {
    artifacts.metadata = options.metadata;
  }

  const payload: StartWorkflowPayload = {
    task: "resume_pipeline",
    artifacts,
  };

  if (options.metadata && Object.keys(options.metadata).length > 0) {
    payload.flags = options.metadata;
  }

  return {
    messagePayload: payload,
    userMessage,
  };
}

function buildAssistantMessage(content: string, status: WorkflowStatus, awaitingApproval: boolean): ChatMessage {
  const cleaned = content.trim();
  const timestamp = nowIso();
  const normalizedContent = cleaned || describeStatus(status, awaitingApproval);
  const tokens = normalizedContent ? [normalizedContent] : [];
  return {
    id: createId("assistant"),
    role: "assistant",
    content: normalizedContent,
    tokens,
    status: "pending",
    createdAt: timestamp,
    metadata: { status },
    error: null,
  };
}

function getStoredWorkflowId(): string | null {
  if (typeof window === "undefined" || !window.localStorage) {
    return null;
  }
  try {
    return window.localStorage.getItem(WORKFLOW_STORAGE_KEY);
  } catch (error) {
    console.warn("Unable to read stored workflow id", error);
    return null;
  }
}

function persistWorkflowId(workflowId: string | null): void {
  if (typeof window === "undefined" || !window.localStorage) {
    return;
  }
  try {
    if (workflowId) {
      window.localStorage.setItem(WORKFLOW_STORAGE_KEY, workflowId);
    } else {
      window.localStorage.removeItem(WORKFLOW_STORAGE_KEY);
    }
  } catch (error) {
    console.warn("Unable to persist workflow id", error);
  }
}

function formatResult(result: unknown): string {
  if (typeof result === "string") {
    return result;
  }
  if (result && typeof result === "object") {
    try {
      return JSON.stringify(result, null, 2);
    } catch (error) {
      console.warn("Failed to stringify workflow result", error);
    }
  }
  return String(result ?? "");
}

function splitContent(content: string): string[] {
  if (!content) return [];
  const cleaned = stripMarkdown(content);
  if (!cleaned) return [];
  return cleaned.split(/\n{2,}/).map((segment) => segment.trim()).filter(Boolean);
}

const initialState: ChatState = {
  messages: [],
  workflowId: null,
  workflowStatus: "idle",
  progress: {},
  draftPreview: null,
  awaitingApproval: false,
  isSubmitting: false,
  isPolling: false,
  error: null,
  approvalError: null,
  connectionStatus: "idle",
  pendingMessageId: null,
};

export function createChatStore() {
  const stateStore = writable<ChatState>({ ...initialState });
  const { subscribe, update, set } = stateStore;

  let pollHandle: ReturnType<typeof setTimeout> | null = null;
  let pollController: AbortController | null = null;
  let hasLoadedPersistedWorkflow = false;
  let resumeWorkflowPromise: Promise<void> | null = null;

  function stopPolling(options: { abort?: boolean } = {}) {
    if (pollHandle) {
      clearTimeout(pollHandle);
      pollHandle = null;
    }
    if (options.abort && pollController) {
      pollController.abort();
      pollController = null;
    }
  }

  function schedulePoll() {
    stopPolling();
    pollHandle = setTimeout(() => {
      void refreshStatus();
    }, POLL_INTERVAL_MS);
  }

  async function refreshStatus(options: { continuePolling?: boolean } = {}) {
    const { continuePolling = true } = options;
    const workflowId = get(stateStore).workflowId;
    if (!workflowId) {
      stopPolling();
      return;
    }

    const controller = new AbortController();
    if (pollController) {
      pollController.abort();
    }
    pollController = controller;

    update((state) => ({ ...state, isPolling: true }));

    try {
      const statusResponse = await getStatus(workflowId, { signal: controller.signal });
      if (controller.signal.aborted) {
        return;
      }
      const workflowState = statusResponse.state;
      const normalizedStatus = normalizeWorkflowStatus(workflowState);
      const awaitingApproval = isAwaitingApprovalState(workflowState);
      const draftPreview = extractDraftFromState(workflowState);
      const progress = computeProgress(get(stateStore).progress, normalizedStatus, awaitingApproval);
      const statusMessage = describeStatus(normalizedStatus, awaitingApproval);

      update((state) => {
        const messages = [...state.messages];
        if (state.pendingMessageId) {
          const index = messages.findIndex((message) => message.id === state.pendingMessageId);
          if (index >= 0) {
            messages[index] = {
              ...messages[index],
              content: statusMessage,
              tokens: statusMessage ? [statusMessage] : [],
              metadata: {
                ...(messages[index].metadata ?? {}),
                status: normalizedStatus,
                stage: workflowState.stage,
              },
              status: normalizedStatus === "complete" ? "complete" : messages[index].status,
            };
          }
        }

        return {
          ...state,
          workflowStatus: normalizedStatus,
          awaitingApproval,
          draftPreview: draftPreview ?? state.draftPreview,
          progress,
          approvalError: null,
          error: null,
          messages,
        };
      });

      if (awaitingApproval) {
        stopPolling();
        update((state) => ({
          ...state,
          draftPreview: draftPreview ?? state.draftPreview,
          workflowStatus: normalizedStatus === "reviewing" ? "awaiting_approval" : normalizedStatus,
        }));
        return;
      }

      if (normalizedStatus === "complete") {
        stopPolling();
        await finalizeWorkflow(workflowId);
        return;
      }

      if (normalizedStatus === "failed") {
        stopPolling();
        update((state) => ({
          ...state,
          error: "Workflow failed",
          workflowStatus: "failed",
          progress: computeProgress(state.progress, "failed", false),
          pendingMessageId: null,
        }));
        return;
      }

      if (continuePolling) {
        schedulePoll();
      }
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }
      stopPolling();
      const message = formatError(error);
      update((state) => ({
        ...state,
        error: message,
        workflowStatus: "failed",
        progress: computeProgress(state.progress, "failed", false),
        pendingMessageId: null,
      }));
      await checkBackendHealth();
    } finally {
      if (pollController === controller) {
        pollController = null;
        update((state) => ({ ...state, isPolling: false }));
      }
    }
  }

  async function finalizeWorkflow(workflowId: string) {
    try {
      const resultResponse = await getResult(workflowId);
      const resultData = extractResultFromState(resultResponse.state);
      const content = formatResult(resultData ?? resultResponse.state);
      const tokens = splitContent(content);

      update((state) => {
        const messages = [...state.messages];
        if (state.pendingMessageId) {
          const index = messages.findIndex((message) => message.id === state.pendingMessageId);
          if (index >= 0) {
            messages[index] = {
              ...messages[index],
              content,
              tokens: tokens.length > 0 ? tokens : [content],
              status: "complete",
              metadata: {
                ...(messages[index].metadata ?? {}),
                result: resultData ?? resultResponse.state,
                state: resultResponse.state,
              },
            };
          }
        } else {
          messages.push({
            id: createId("assistant"),
            role: "assistant",
            content,
            tokens: tokens.length > 0 ? tokens : [content],
            status: "complete",
            createdAt: nowIso(),
            metadata: { result: resultData ?? resultResponse.state, state: resultResponse.state },
            error: null,
          });
        }

        return {
          ...state,
          messages,
          workflowStatus: "complete" as WorkflowStatus,
          progress: computeProgress(state.progress, "complete", false),
          awaitingApproval: false,
          draftPreview: null,
          pendingMessageId: null,
        };
      });
    } catch (error) {
      const message = formatError(error);
      update((state) => ({
        ...state,
        error: message,
        workflowStatus: "failed",
        progress: computeProgress(state.progress, "failed", false),
        pendingMessageId: null,
      }));
      await checkBackendHealth();
    }
  }

  async function checkBackendHealth(): Promise<boolean> {
    update((state) => ({ ...state, connectionStatus: "idle" }));
    try {
      await getHealth();
      update((state) => ({ ...state, connectionStatus: "connected" }));
      if (!hasLoadedPersistedWorkflow) {
        await resumeStoredWorkflow();
      }
      return true;
    } catch (error) {
      console.warn("Backend health check failed", error);
      update((state) => ({ ...state, connectionStatus: "error" }));
      return false;
    }
  }

  async function resumeStoredWorkflow(): Promise<void> {
    if (hasLoadedPersistedWorkflow) {
      return;
    }

    if (!resumeWorkflowPromise) {
      resumeWorkflowPromise = (async () => {
        const storedWorkflowId = getStoredWorkflowId();
        if (storedWorkflowId) {
          update((state) => ({
            ...state,
            workflowId: storedWorkflowId,
            workflowStatus: "unknown",
          }));

          await refreshStatus();
        }

        hasLoadedPersistedWorkflow = true;
      })().finally(() => {
        resumeWorkflowPromise = null;
      });
    }

    await resumeWorkflowPromise;
  }

  return {
    subscribe,
    async initialize() {
      const healthy = await checkBackendHealth();
      if (!healthy) {
        return;
      }

      await resumeStoredWorkflow();
    },
    async sendMessage(options: SendMessageOptions) {
      if (get(stateStore).workflowId) {
        return;
      }

      const trimmedContent = options.content?.trim() ?? "";
      const hasFiles = Boolean(options.files && options.files.length > 0);
      if (trimmedContent.length === 0 && !hasFiles) {
        return;
      }

      const { messagePayload, userMessage } = await preparePayload(options);

      if (userMessage) {
        update((state) => ({
          ...state,
          messages: [...state.messages, userMessage],
        }));
      }

      if (get(stateStore).connectionStatus !== "connected") {
        const healthy = await checkBackendHealth();
        if (!healthy) {
          return;
        }
      }

      update((state) => ({
        ...state,
        isSubmitting: true,
        error: null,
        approvalError: null,
        connectionStatus: "connected",
      }));

      try {
        const response = await startWorkflow(messagePayload);
        const workflowId = response.workflow_id;
        const normalizedStatus: WorkflowStatus = "drafting";
        const awaitingApproval = false;
        const assistantMessage = buildAssistantMessage(
          describeStatus(normalizedStatus, awaitingApproval),
          normalizedStatus,
          awaitingApproval,
        );

        update((state) => ({
          ...state,
          workflowId,
          workflowStatus: normalizedStatus,
          messages: [
            ...state.messages,
            {
              ...assistantMessage,
              metadata: { ...(assistantMessage.metadata ?? {}), run_id: response.run_id },
            },
          ],
          pendingMessageId: assistantMessage.id,
          progress: computeProgress(state.progress, normalizedStatus, awaitingApproval),
          awaitingApproval,
          draftPreview: awaitingApproval ? "" : state.draftPreview,
        }));

        persistWorkflowId(workflowId);

        await refreshStatus();
      } catch (error) {
        const message = formatError(error);
        update((state) => ({
          ...state,
          error: message,
          workflowStatus: "failed",
          progress: computeProgress(state.progress, "failed", false),
          pendingMessageId: null,
        }));
        await checkBackendHealth();
      } finally {
        update((state) => ({ ...state, isSubmitting: false }));
      }
    },
    async submitApproval(approved: boolean, feedback?: string) {
      const state = get(stateStore);
      if (!state.workflowId || !state.awaitingApproval) {
        return;
      }

      update((current) => ({ ...current, approvalError: null, isPolling: true }));

      try {
        await submitApproval(state.workflowId, { approved, notes: feedback ?? null });
        update((current) => ({
          ...current,
          awaitingApproval: false,
          draftPreview: null,
          progress: computeProgress(current.progress, current.workflowStatus, false),
        }));
        schedulePoll();
      } catch (error) {
        update((current) => ({
          ...current,
          approvalError: formatError(error),
        }));
      } finally {
        update((current) => ({ ...current, isPolling: false }));
      }
    },
    clearError() {
      update((state) => ({ ...state, error: null, approvalError: null }));
    },
    reset() {
      persistWorkflowId(null);
      stopPolling({ abort: true });
      const { connectionStatus } = get(stateStore);
      set({ ...initialState, connectionStatus });
      void checkBackendHealth();
    },
    async checkConnection() {
      await checkBackendHealth();
    },
  };
}

export const chatStore = createChatStore();
