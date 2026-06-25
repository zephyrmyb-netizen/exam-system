import { readonly, ref, type Ref, type DeepReadonly } from "vue";

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

const visible = ref<boolean>(false);
const options = ref<ConfirmOptions>({
  title: "",
  message: "",
  confirmText: "确定",
  cancelText: "取消",
  tone: "default",
});

let pendingResolve: ((value: boolean) => void) | null = null;

function close(result: boolean): void {
  visible.value = false;
  if (pendingResolve) {
    pendingResolve(result);
    pendingResolve = null;
  }
}

export function useConfirmDialog(): ConfirmDialogReturn {
  function confirm(nextOptions: Partial<ConfirmOptions> = {}): Promise<boolean> {
    if (pendingResolve) {
      close(false);
    }

    options.value = {
      title: nextOptions.title || "确认操作",
      message: nextOptions.message || "",
      confirmText: nextOptions.confirmText || "确定",
      cancelText: nextOptions.cancelText || "取消",
      tone: nextOptions.tone || "default",
    };
    visible.value = true;

    return new Promise<boolean>((resolve) => {
      pendingResolve = resolve;
    });
  }

  return {
    visible: readonly(visible),
    options: readonly(options),
    confirm,
    accept: () => close(true),
    cancel: () => close(false),
  };
}
