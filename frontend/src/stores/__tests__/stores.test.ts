import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useAiImportTask, useAiImportTaskStore } from "../aiImportTask";
import { useAuth, useAuthStore } from "../auth";
import { useConfirmDialog, useConfirmDialogStore } from "../confirmDialog";

describe("pinia-backed stores", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("keeps the auth composable ref-shaped API", () => {
    const store = useAuthStore();
    const auth = useAuth();

    expect(auth.user.value).toBe(null);
    expect(auth.loading.value).toBe(false);
    expect(auth.fetchProfile).toBe(store.fetchProfile);
  });

  it("keeps the AI import task composable ref-shaped API", () => {
    const store = useAiImportTaskStore();
    const task = useAiImportTask();

    expect(task.status.value).toBe("idle");
    expect(task.progressTitle.value).toBe("AI 导入");
    expect(task.reset).toBe(store.reset);
  });

  it("keeps the confirm dialog composable API", async () => {
    const store = useConfirmDialogStore();
    const dialog = useConfirmDialog();

    const pending = dialog.confirm({ title: "确认", message: "继续？" });
    expect(dialog.visible.value).toBe(true);
    expect(dialog.options.value.title).toBe("确认");
    expect(dialog.accept).toBe(store.accept);

    dialog.accept();
    await expect(pending).resolves.toBe(true);
  });
});
