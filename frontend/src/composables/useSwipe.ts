import { onMounted, onUnmounted, type Ref } from "vue";

export interface SwipeOptions {
  threshold?: number;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
}

export function useSwipe(target: Ref<HTMLElement | null>, options: SwipeOptions) {
  const threshold = options.threshold ?? 50;
  let startX = 0;
  let startY = 0;
  let tracking = false;

  function onTouchStart(event: TouchEvent) {
    if (event.touches.length !== 1) return;
    startX = event.touches[0].clientX;
    startY = event.touches[0].clientY;
    tracking = true;
  }

  function onTouchEnd(event: TouchEvent) {
    if (!tracking) return;
    tracking = false;
    const dx = event.changedTouches[0].clientX - startX;
    const dy = event.changedTouches[0].clientY - startY;
    if (Math.abs(dx) < threshold || Math.abs(dy) > Math.abs(dx)) return;
    if (dx < 0) options.onSwipeLeft?.();
    else options.onSwipeRight?.();
  }

  onMounted(() => {
    target.value?.addEventListener("touchstart", onTouchStart, { passive: true });
    target.value?.addEventListener("touchend", onTouchEnd, { passive: true });
  });

  onUnmounted(() => {
    target.value?.removeEventListener("touchstart", onTouchStart);
    target.value?.removeEventListener("touchend", onTouchEnd);
  });
}
