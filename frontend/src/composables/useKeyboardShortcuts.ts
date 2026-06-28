export interface ShortcutHandlers {
  next?: () => void;
  prev?: () => void;
  submit?: () => void;
  selectOption?: (index: number) => void;
}

const NEXT_KEYS = new Set(["ArrowRight", "d", "D"]);
const PREV_KEYS = new Set(["ArrowLeft", "a", "A"]);

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) || target.isContentEditable;
}

export function useKeyboardShortcuts(handlers: ShortcutHandlers) {
  function onKeydown(event: KeyboardEvent) {
    if (isTypingTarget(event.target)) return;

    if (NEXT_KEYS.has(event.key)) {
      event.preventDefault();
      handlers.next?.();
      return;
    }
    if (PREV_KEYS.has(event.key)) {
      event.preventDefault();
      handlers.prev?.();
      return;
    }
    if (event.key === "Enter") {
      handlers.submit?.();
      return;
    }
    if (/^[1-5]$/.test(event.key)) {
      handlers.selectOption?.(Number(event.key) - 1);
    }
  }

  function bind() {
    window.addEventListener("keydown", onKeydown);
  }

  function unbind() {
    window.removeEventListener("keydown", onKeydown);
  }

  return { bind, unbind };
}
