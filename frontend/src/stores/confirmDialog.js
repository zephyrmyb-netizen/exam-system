import { readonly, ref } from "vue";

const visible = ref(false);
const options = ref({
  title: "",
  message: "",
  confirmText: "确定",
  cancelText: "取消",
  tone: "default",
});

let pendingResolve = null;

function close(result) {
  visible.value = false;
  if (pendingResolve) {
    pendingResolve(result);
    pendingResolve = null;
  }
}

export function useConfirmDialog() {
  function confirm(nextOptions = {}) {
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

    return new Promise((resolve) => {
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
