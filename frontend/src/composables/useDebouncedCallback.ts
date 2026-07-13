import { getCurrentScope, onScopeDispose } from "vue";

/** Schedule a local-only update without issuing one request per keystroke. */
export function useDebouncedCallback<Args extends unknown[]>(
  callback: (...args: Args) => void,
  delay = 260,
) {
  let timer: ReturnType<typeof setTimeout> | null = null;

  function cancel(): void {
    if (!timer) return;
    clearTimeout(timer);
    timer = null;
  }

  function schedule(...args: Args): void {
    cancel();
    timer = setTimeout(() => {
      timer = null;
      callback(...args);
    }, delay);
  }

  if (getCurrentScope()) onScopeDispose(cancel);

  return { cancel, schedule };
}
