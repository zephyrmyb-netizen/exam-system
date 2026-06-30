import { describe, expect, it } from "vitest";
import request, { getErrorMessage, getToken, resolveDefaultApiBaseUrl, setToken } from "../request.ts";

function axiosLikeError(status: number) {
  return {
    isAxiosError: true,
    response: {
      status,
      data: {},
    },
  };
}

describe("resolveDefaultApiBaseUrl", () => {
  it("uses same-origin API calls when a phone opens the Vite dev server by LAN IP", () => {
    expect(resolveDefaultApiBaseUrl({ hostname: "192.168.10.14", port: "5174", protocol: "http:" })).toBe("");
  });

  it("keeps same-origin API calls for the production nginx port", () => {
    expect(resolveDefaultApiBaseUrl({ hostname: "192.168.10.14", port: "8080", protocol: "http:" })).toBe("");
  });

  it("uses same-origin API calls for localhost development through the Vite proxy", () => {
    expect(resolveDefaultApiBaseUrl({ hostname: "localhost", port: "5174", protocol: "http:" })).toBe("");
  });
});

describe("getErrorMessage", () => {
  it("shows a clear AI timeout message for 504 responses", () => {
    expect(getErrorMessage(axiosLikeError(504))).toContain("超时");
  });
});

describe("request auth handling", () => {
  it("keeps the token for server-side AI failures", async () => {
    setToken("still-valid");

    await expect(
      request.get("/ai-failed", {
        adapter: () => Promise.reject(axiosLikeError(502)),
      }),
    ).rejects.toMatchObject({ response: { status: 502 } });

    expect(getToken()).toBe("still-valid");
  });

  it("clears the token only for 401 auth failures", async () => {
    setToken("expired");

    await expect(
      request.get("/auth-failed", {
        adapter: () => Promise.reject(axiosLikeError(401)),
      }),
    ).rejects.toMatchObject({ response: { status: 401 } });

    expect(getToken()).toBe("");
  });
});
