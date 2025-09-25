export type ChatRole = "user" | "assistant" | "system";

export interface AttachmentPayload {
  id: string;
  name: string;
  type: string;
  size: number;
  data?: string;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  tokens: string[];
  status: "pending" | "complete" | "error";
  createdAt: string;
  metadata?: Record<string, unknown>;
  error?: string | null;
  attachments?: AttachmentPayload[];
}

export type WorkflowStatus =
  | "idle"
  | "drafting"
  | "reviewing"
  | "awaiting_approval"
  | "compliance"
  | "complete"
  | "failed"
  | "unknown";

export interface ProgressRecord {
  node: string;
  status: "pending" | "running" | "complete" | "error";
  data?: unknown;
  timestamp: string;
}

export interface ChatState {
  messages: ChatMessage[];
  workflowId: string | null;
  workflowStatus: WorkflowStatus;
  progress: Record<string, ProgressRecord>;
  draftPreview: unknown;
  awaitingApproval: boolean;
  isSubmitting: boolean;
  isPolling: boolean;
  error: string | null;
  approvalError: string | null;
  connectionStatus: "idle" | "connected" | "error";
  pendingMessageId: string | null;
}

export interface SendMessageOptions {
  content: string;
  files?: File[];
  metadata?: Record<string, unknown>;
}

export type ResumeTask =
  | "ingest"
  | "draft"
  | "revise"
  | "resume_pipeline"
  | "compliance_only"
  | "publish";

export type ResumeStage =
  | "route"
  | "ingestion"
  | "drafting"
  | "critique"
  | "revision"
  | "compliance"
  | "publishing"
  | "done";

export type ResumeStatus = "pending" | "in_progress" | "complete" | "error";

export interface ResumeMessage {
  role: "human" | "assistant" | "system";
  content: string;
  model?: string | null;
}

export interface ResumeWorkflowState {
  task: ResumeTask;
  stage?: ResumeStage;
  status?: ResumeStatus;
  request_id: string;
  messages?: ResumeMessage[];
  artifacts?: Record<string, unknown> | null;
  audit_trail?: string[];
  metrics?: Record<string, number>;
  flags?: Record<string, unknown> | null;
}

export interface StartWorkflowPayload {
  task?: ResumeTask;
  artifacts?: Record<string, unknown>;
  flags?: Record<string, unknown>;
  request_id?: string | null;
}

export interface StartWorkflowResponse {
  workflow_id: string;
  run_id: string | null;
}

export interface WorkflowStateResponse {
  state: ResumeWorkflowState;
}

export interface SubmitApprovalPayload {
  approved: boolean;
  notes?: string | null;
}

export interface WorkflowResultResponse {
  state: ResumeWorkflowState;
}

export interface HealthResponse {
  status: string;
}
