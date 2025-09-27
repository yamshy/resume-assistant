import { afterEach, describe, expect, it, vi } from "vitest";

import { startWorkflow, submitApproval } from "./resume";

describe("resume API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("throws a descriptive error when a response is unexpectedly empty", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 200, statusText: "OK" }),
    );

    await expect(startWorkflow({})).rejects.toThrowError(
      /Expected response body but received empty response/,
    );
  });

  it("allows endpoints to opt into empty responses", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(null, { status: 204, statusText: "No Content" }),
    );

    await expect(
      submitApproval("workflow-123", { approved: true }),
    ).resolves.toBeUndefined();
  });
});
