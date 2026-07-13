import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import request from "../../api/request";
import { useManualQuestionImport } from "../useManualQuestionImport";

vi.mock("../../api/request", () => ({
  default: {
    post: vi.fn(),
  },
  getErrorMessage: (_error: unknown, fallback: string) => fallback,
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((next) => {
    resolve = next;
  });
  return { promise, resolve };
}

describe("useManualQuestionImport duplicate submission protection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("posts one batch when importQuestions is called repeatedly before the request settles", async () => {
    const pending = deferred<{ data: { imported_count: number; course_id: number } }>();
    vi.mocked(request.post).mockReturnValue(pending.promise);
    const manualImport = useManualQuestionImport(ref(7));

    const first = manualImport.importQuestions();
    const second = manualImport.importQuestions();

    expect(manualImport.importLoading.value).toBe(true);
    expect(request.post).toHaveBeenCalledTimes(1);

    pending.resolve({ data: { imported_count: 1, course_id: 7 } });
    await Promise.all([first, second]);

    expect(manualImport.importLoading.value).toBe(false);
    expect(manualImport.importMessage.value).toContain("导入成功");
  });
});
