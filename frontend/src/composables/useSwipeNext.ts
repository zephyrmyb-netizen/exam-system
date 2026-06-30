import { onBeforeUnmount, onMounted, ref, type Ref } from "vue";

interface UseSwipeNextOptions {
  /** 触发回调（一般传入下一题函数） */
  onSwipe: () => void;
  /** 横向位移阈值（px），默认 80 */
  threshold?: number;
  /** 是否启用，传入 ref 控制启停（如仅在 result 显示时响应） */
  enabled?: Ref<boolean>;
}

/**
 * 原生 pointer events 实现的"从右往左滑 -> 下一题"手势。
 *
 * 触发条件：
 * 1. pointerdown 起点记录
 * 2. pointerup 时计算位移：横向 dx < 0（向左滑）且 |dx| >= threshold
 * 3. 横向位移绝对值 > 纵向位移绝对值（避免误识别上下滑）
 *
 * 兼容鼠标 / 触屏（pointer events 在主流浏览器都已支持）。
 */
export function useSwipeNext(options: UseSwipeNextOptions): void {
  const { onSwipe, threshold = 80, enabled } = options;

  let startX = 0;
  let startY = 0;
  let tracking = false;

  function onPointerDown(event: PointerEvent): void {
    if (enabled && !enabled.value) return;
    // 仅主键 / 触摸
    if (event.button !== 0 && event.pointerType === "mouse") return;
    startX = event.clientX;
    startY = event.clientY;
    tracking = true;
  }

  function onPointerUp(event: PointerEvent): void {
    if (!tracking) return;
    tracking = false;
    if (enabled && !enabled.value) return;

    const dx = event.clientX - startX;
    const dy = event.clientY - startY;
    const absDx = Math.abs(dx);
    const absDy = Math.abs(dy);

    // 从右往左滑：dx < 0；横向位移大于纵向；超过阈值
    if (dx < 0 && absDx >= threshold && absDx > absDy) {
      onSwipe();
    }
  }

  function onPointerCancel(): void {
    tracking = false;
  }

  onMounted(() => {
    window.addEventListener("pointerdown", onPointerDown, { passive: true });
    window.addEventListener("pointerup", onPointerUp, { passive: true });
    window.addEventListener("pointercancel", onPointerCancel, { passive: true });
  });

  onBeforeUnmount(() => {
    window.removeEventListener("pointerdown", onPointerDown);
    window.removeEventListener("pointerup", onPointerUp);
    window.removeEventListener("pointercancel", onPointerCancel);
  });
}

/** 给 UI 显示用的"用户是否在滑动"指示器（可选） */
export function useSwipeProgress(enabled: Ref<boolean>): Ref<number> {
  const progress = ref(0);
  let startX = 0;
  let startY = 0;
  let tracking = false;

  function onPointerDown(event: PointerEvent): void {
    if (!enabled.value) return;
    if (event.button !== 0 && event.pointerType === "mouse") return;
    startX = event.clientX;
    startY = event.clientY;
    tracking = true;
    progress.value = 0;
  }

  function onPointerMove(event: PointerEvent): void {
    if (!tracking) return;
    const dx = event.clientX - startX;
    const dy = event.clientY - startY;
    if (dx >= 0) {
      progress.value = 0;
      return;
    }
    if (Math.abs(dx) <= Math.abs(dy)) {
      progress.value = 0;
      return;
    }
    progress.value = Math.min(1, Math.abs(dx) / 80);
  }

  function onPointerUp(): void {
    tracking = false;
    progress.value = 0;
  }

  onMounted(() => {
    window.addEventListener("pointerdown", onPointerDown, { passive: true });
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerup", onPointerUp, { passive: true });
    window.addEventListener("pointercancel", onPointerUp, { passive: true });
  });

  onBeforeUnmount(() => {
    window.removeEventListener("pointerdown", onPointerDown);
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", onPointerUp);
    window.removeEventListener("pointercancel", onPointerUp);
  });

  return progress;
}
