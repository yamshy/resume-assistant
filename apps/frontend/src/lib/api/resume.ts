import { API_URL } from "../chat/config";
import type {
  HealthResponse,
  StartWorkflowPayload,
  StartWorkflowResponse,
  SubmitApprovalPayload,
  WorkflowResultResponse,
  WorkflowStateResponse,
} from "../chat/types";

interface HandleResponseOptions {
  allowEmpty?: boolean;
}

async function handleResponse<T>(response: Response, options: HandleResponseOptions = {}): Promise<T> {
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    const message = text ? `${response.status} ${response.statusText} - ${text}` : `${response.status} ${response.statusText}`;
    throw new Error(message.trim());
  }
  const text = await response.text().catch(() => "");
  if (!text.trim()) {
    if (options.allowEmpty) {
      return undefined as T;
    }

    const statusSummary = `${response.status} ${response.statusText}`.trim();
    const errorMessage = statusSummary
      ? `${statusSummary} - Expected response body but received empty response.`
      : "Expected response body but received empty response.";
    throw new Error(errorMessage);
  }

  try {
    return JSON.parse(text) as T;
  } catch (error) {
    console.warn("Failed to parse JSON response", error);
    return text as unknown as T;
  }
}

export async function startWorkflow(data: StartWorkflowPayload): Promise<StartWorkflowResponse> {
  const response = await fetch(`${API_URL}/workflows/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<StartWorkflowResponse>(response);
}

export async function getStatus(
  workflowId: string,
  options: { signal?: AbortSignal } = {},
): Promise<WorkflowStateResponse> {
  const response = await fetch(`${API_URL}/workflows/${encodeURIComponent(workflowId)}`, {
    method: "GET",
    signal: options.signal,
  });
  return handleResponse<WorkflowStateResponse>(response);
}

export async function submitApproval(
  workflowId: string,
  payload: SubmitApprovalPayload,
): Promise<void> {
  const response = await fetch(`${API_URL}/workflows/${encodeURIComponent(workflowId)}/approval`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await handleResponse<void>(response, { allowEmpty: true });
}

export async function getResult(workflowId: string): Promise<WorkflowResultResponse> {
  const response = await fetch(`${API_URL}/workflows/${encodeURIComponent(workflowId)}/result`, {
    method: "GET",
  });
  return handleResponse<WorkflowResultResponse>(response);
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/health`, {
    method: "GET",
  });
  return handleResponse<HealthResponse>(response);
}
