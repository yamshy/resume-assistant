import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ChatState, WorkflowStateResponse } from '../types';
import { WORKFLOW_STORAGE_KEY } from '../config';

vi.mock('../../api/resume', () => ({
  startWorkflow: vi.fn(),
  getStatus: vi.fn(),
  getResult: vi.fn(),
  submitApproval: vi.fn(),
  getHealth: vi.fn(),
}));

import { getStatus, getResult, startWorkflow, submitApproval, getHealth } from '../../api/resume';
import { createChatStore } from '../stores';

const startWorkflowMock = vi.mocked(startWorkflow);
const getStatusMock = vi.mocked(getStatus);
const getResultMock = vi.mocked(getResult);
const submitApprovalMock = vi.mocked(submitApproval);
const getHealthMock = vi.mocked(getHealth);

const collectState = (store: ReturnType<typeof createChatStore>) => {
  let current: ChatState;
  const unsubscribe = store.subscribe((state) => {
    current = state;
  });
  return { getState: () => current!, unsubscribe };
};

beforeEach(() => {
  vi.useFakeTimers();
  startWorkflowMock.mockReset();
  getStatusMock.mockReset();
  getResultMock.mockReset();
  submitApprovalMock.mockReset();
  getHealthMock.mockReset();

  getHealthMock.mockResolvedValue({ status: 'ok' });

  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.clear();
  }

  let counter = 0;
  vi.stubGlobal('crypto', {
    randomUUID: () => `uuid-${counter++}`,
  });

  vi.setSystemTime(new Date('2024-01-01T00:00:00Z'));
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('chat store', () => {
  it('starts a workflow and records awaiting approval state', async () => {
    const store = createChatStore();
    const { getState, unsubscribe } = collectState(store);

    startWorkflowMock.mockResolvedValue({ workflow_id: 'wf-123', run_id: 'run-123' });
    getStatusMock.mockResolvedValue({
      state: {
        task: 'resume_pipeline',
        stage: 'revision',
        status: 'in_progress',
        request_id: 'req-123',
        artifacts: { draft_resume: 'Draft content' },
      },
    });

    await store.sendMessage({ content: 'Help with my resume' });

    const state = getState();
    expect(startWorkflowMock).toHaveBeenCalledWith({
      task: 'resume_pipeline',
      artifacts: {
        messages: [
          {
            role: 'human',
            content: 'Help with my resume',
            model: null,
          },
        ],
      },
    });
    expect(state.workflowId).toBe('wf-123');
    expect(state.awaitingApproval).toBe(true);
    expect(state.draftPreview).toBe('Draft content');
    expect(state.workflowStatus).toBe('awaiting_approval');
    expect(state.messages.some((message) => message.metadata?.status === 'awaiting_approval')).toBe(true);

    unsubscribe();
  });

  it('fetches workflow results once the run completes', async () => {
    const store = createChatStore();
    const { getState, unsubscribe } = collectState(store);

    startWorkflowMock.mockResolvedValue({ workflow_id: 'wf-456', run_id: 'run-456' });
    getStatusMock
      .mockResolvedValueOnce({
        state: {
          task: 'resume_pipeline',
          stage: 'drafting',
          status: 'in_progress',
          request_id: 'req-456',
        },
      })
      .mockResolvedValueOnce({
        state: {
          task: 'resume_pipeline',
          stage: 'done',
          status: 'complete',
          request_id: 'req-456',
          artifacts: { final_resume: 'Final resume output' },
        },
      });
    getResultMock.mockResolvedValue({
      state: {
        task: 'resume_pipeline',
        stage: 'done',
        status: 'complete',
        request_id: 'req-456',
        artifacts: { final_resume: 'Final resume output' },
      },
    });

    await store.sendMessage({ content: 'Create a resume' });

    await vi.runOnlyPendingTimersAsync();

    const state = getState();
    expect(getStatusMock.mock.calls.some(([workflowId]) => workflowId === 'wf-456')).toBe(true);
    for (const [, options] of getStatusMock.mock.calls) {
      expect(options?.signal).toBeInstanceOf(AbortSignal);
    }
    expect(getResultMock).toHaveBeenCalledWith('wf-456');
    expect(state.workflowStatus).toBe('complete');
    const assistantMessage = state.messages.find((message) => message.role === 'assistant' && message.status === 'complete');
    expect(assistantMessage?.content).toBe('Final resume output');
    expect(state.pendingMessageId).toBeNull();

    unsubscribe();
  });

  it('submits approval feedback and resumes polling', async () => {
    const store = createChatStore();
    const { getState, unsubscribe } = collectState(store);

    startWorkflowMock.mockResolvedValue({ workflow_id: 'wf-789', run_id: 'run-789' });
    getStatusMock.mockResolvedValueOnce({
      state: {
        task: 'resume_pipeline',
        stage: 'revision',
        status: 'in_progress',
        request_id: 'req-789',
        artifacts: { draft_resume: 'Needs review' },
      },
    });

    await store.sendMessage({ content: 'Review my resume' });

    getStatusMock.mockResolvedValueOnce({
      state: {
        task: 'resume_pipeline',
        stage: 'drafting',
        status: 'in_progress',
        request_id: 'req-789',
      },
    });
    submitApprovalMock.mockResolvedValue();

    const awaitingState = getState();
    expect(awaitingState.workflowId).toBe('wf-789');
    expect(awaitingState.awaitingApproval).toBe(true);

    await store.submitApproval(true, 'Looks good');
    await vi.runOnlyPendingTimersAsync();

    expect(submitApprovalMock).toHaveBeenCalledWith('wf-789', {
      approved: true,
      notes: 'Looks good',
    });

    const state = getState();
    expect(state.awaitingApproval).toBe(false);
    expect(state.draftPreview).toBeNull();
    expect(state.workflowStatus).toBe('drafting');

    unsubscribe();
  });

  it('ignores polling responses after the workspace is reset', async () => {
    const store = createChatStore();
    const { getState, unsubscribe } = collectState(store);

    startWorkflowMock.mockResolvedValue({ workflow_id: 'wf-reset', run_id: 'run-reset' });
    getStatusMock.mockResolvedValueOnce({
      state: {
        task: 'resume_pipeline',
        stage: 'drafting',
        status: 'in_progress',
        request_id: 'req-reset-1',
      },
    });

    await store.sendMessage({ content: 'Reset me' });

    let resolvePoll: ((value: WorkflowStateResponse) => void) | undefined;
    getStatusMock.mockImplementationOnce((workflowId, options) => {
      expect(workflowId).toBe('wf-reset');
      expect(options?.signal).toBeInstanceOf(AbortSignal);
      return new Promise<WorkflowStateResponse>((resolve) => {
        resolvePoll = resolve;
      });
    });

    await vi.runOnlyPendingTimersAsync();

    expect(resolvePoll).toBeDefined();

    store.reset();

    resolvePoll?.({
      state: {
        task: 'resume_pipeline',
        stage: 'drafting',
        status: 'in_progress',
        request_id: 'req-reset-2',
        artifacts: { draft_resume: 'Stale draft' },
      },
    });

    await Promise.resolve();

    const state = getState();
    expect(state.workflowId).toBeNull();
    expect(state.messages).toHaveLength(0);
    expect(state.awaitingApproval).toBe(false);
    expect(state.workflowStatus).toBe('idle');

    unsubscribe();
  });

  it('resumes a persisted workflow after recovering from an offline initialization', async () => {
    const originalWindow = globalThis.window;
    const originalLocalStorage = originalWindow?.localStorage;
    const storage = new Map<string, string>();

    const localStorageMock: Storage = {
      getItem: (key) => storage.get(key) ?? null,
      setItem: (key, value) => {
        storage.set(key, value);
      },
      removeItem: (key) => {
        storage.delete(key);
      },
      clear: () => {
        storage.clear();
      },
      key: (index) => Array.from(storage.keys())[index] ?? null,
      get length() {
        return storage.size;
      },
    };

    if (originalWindow) {
      Object.defineProperty(originalWindow, 'localStorage', {
        configurable: true,
        value: localStorageMock,
      });
    } else {
      globalThis.window = {
        localStorage: localStorageMock,
      } as Window & typeof globalThis;
    }

    try {
      window.localStorage.setItem(WORKFLOW_STORAGE_KEY, 'wf-offline');

      getHealthMock.mockRejectedValueOnce(new Error('offline'));
      getStatusMock.mockResolvedValue({
        state: {
          task: 'resume_pipeline',
          stage: 'drafting',
          status: 'in_progress',
          request_id: 'req-offline',
        },
      });

      const store = createChatStore();
      const { getState, unsubscribe } = collectState(store);

      await store.initialize();

      expect(getState().workflowId).toBeNull();
      expect(getStatusMock).not.toHaveBeenCalled();

      await store.checkConnection();

      const state = getState();
      expect(getStatusMock.mock.calls.some(([workflowId]) => workflowId === 'wf-offline')).toBe(true);
      for (const [, options] of getStatusMock.mock.calls) {
        expect(options?.signal).toBeInstanceOf(AbortSignal);
      }
      expect(state.workflowId).toBe('wf-offline');
      expect(state.workflowStatus).toBe('drafting');

      unsubscribe();
    } finally {
      if (originalWindow) {
        if (originalLocalStorage) {
          Object.defineProperty(originalWindow, 'localStorage', {
            configurable: true,
            value: originalLocalStorage,
          });
        } else {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          delete (originalWindow as any).localStorage;
        }
      } else {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        delete (globalThis as any).window;
      }
    }
  });
});
