import { type DeepReadonly, type Ref, readonly } from "vue";
import { defineStore, storeToRefs } from "pinia";

export type ConfirmTone = "default" | "danger" | "warning";

export interface ConfirmOptions {
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  tone: ConfirmTone;
}

export interface ConfirmDialogReturn {
  visible: DeepReadonly<Ref<boolean>>;
  options: DeepReadonly<Ref<ConfirmOptions>>;
  confirm: (nextOptions?: Partial<ConfirmOptions>) => Promise<boolean>;
  accept: () => void;
  cancel: () => void;
}

let pendingResolve: ((value: boolean) => void) | null = null;

export const useConfirmDialogStore = defineStore("confirmDialog", {
  state: () => ({
    visible: false,
    options: {
      title: "",
      message: "",
      confirmText: "确定",
      cancelText: "取消",
      tone: "default" as ConfirmTone,
    },
  }),
  actions: {
    close(result: boolean): void {
      this.visible = false;
      if (pendingResolve) {
        pendingResolve(result);
        pendingResolve = null;
      }
    },

    confirm(nextOptions: Partial<ConfirmOptions> = {}): Promise<boolean> {
      if (pendingResolve) {
        this.close(false);
      }

      this.options = {
        title: nextOptions.title || "确认操作",
        message: nextOptions.message || "",
        confirmText: nextOptions.confirmText || "确定",
        cancelText: nextOptions.cancelText || "取消",
        tone: nextOptions.tone || "default",
      };
      this.visible = true;

      return new Promise<boolean>((resolve) => {
        pendingResolve = resolve;
      });
    },

    accept(): void {
      this.close(true);
    },

    cancel(): void {
      this.close(false);
    },
  },
});

export function useConfirmDialog(): ConfirmDialogReturn {
  const store = useConfirmDialogStore();
  const refs = storeToRefs(store);
  return {
    visible: readonly(refs.visible),
    options: readonly(refs.options),
    confirm: store.confirm,
    accept: store.accept,
    cancel: store.cancel,
  };
}
