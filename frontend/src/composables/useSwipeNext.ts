import { onBeforeUnmount, onMounted, ref, watch, type Ref } from "vue";

interface UseSwipeNextOptions {
  /** 触发回调（一般传入下一题函数） */
  onSwipe: () => void;
  /** 横向位移阈值（px），默认 64，避免纵向滚动时误触 */
  threshold?: number;
  /** 是否启用，传入 ref 控制启停（如仅在 result 显示时响应） */
  enabled?: Ref<boolean>;
  /** 跟手进度 ref（可选），0~1，用于UI反馈 */
  progress?: Ref<number>;
  /** Bind the gesture to the practice surface instead of the entire window. */
  target?: Ref<HTMLElement | null>;
}

/**
 * 原生 pointer events 实现的"从右往左滑 -> 下一题"手势。
 *
 * 触发条件（满足任一即触发，让滑动更灵敏）：
 * 1. 位移触发：dx < 0 且 |dx| >= threshold 且横向位移明显大于纵向位移。
 * 2. 速度触发：dx < 0 且 |dx| >= 36 且速度 > 0.65 px/ms，并保持横向主导。
 *
 * 同时通过 progress ref 实时输出滑动进度（0~1），用于跟手视觉反馈。
 */
export function useSwipeNext(options: UseSwipeNextOptions): void {
  const { onSwipe, threshold = 64, enabled, progress, target } = options;

  let startX = 0;
  let startY = 0;
  let startTime = 0;
  let tracking = false;
  let lastX = 0;
  let lastTime = 0;
  let velocity = 0;

  function isEnabled(): boolean {
    return !enabled || enabled.value;
  }

  let pointerId: number | null = null;
  let attachedTarget: HTMLElement | null = null;

  function onPointerDown(event: PointerEvent): void {
    if (!isEnabled()) return;
    // 仅主键 / 触摸
    if (event.button !== 0 && event.pointerType === "mouse") return;
    if (event.target instanceof Element && event.target.closest("button, input, textarea, select, a")) return;
    startX = event.clientX;
    startY = event.clientY;
    lastX = event.clientX;
    startTime = performance.now();
    lastTime = startTime;
    velocity = 0;
    tracking = true;
    pointerId = event.pointerId;
    if (progress) progress.value = 0;
  }

  function onPointerMove(event: PointerEvent): void {
    if (!tracking || event.pointerId !== pointerId || !isEnabled()) return;
    const dx = event.clientX - startX;
    const dy = event.clientY - startY;
    // 实时计算速度
    const now = performance.now();
    const dt = now - lastTime;
    if (dt > 0) {
      const dxInstant = event.clientX - lastX;
      // 指数平滑，避免抖动
      velocity = velocity * 0.6 + (dxInstant / dt) * 0.4;
    }
    lastX = event.clientX;
    lastTime = now;

    // 仅向左滑且横向占主导时才更新进度
    if (dx < 0 && Math.abs(dx) >= Math.abs(dy) * 1.25) {
      if (progress) progress.value = Math.min(1, Math.abs(dx) / threshold);
    } else if (progress) {
      progress.value = 0;
    }
  }

  function onPointerUp(event: PointerEvent): void {
    if (!tracking || event.pointerId !== pointerId) return;
    tracking = false;
    pointerId = null;
    if (!isEnabled()) {
      if (progress) progress.value = 0;
      return;
    }

    const dx = event.clientX - startX;
    const dy = event.clientY - startY;
    const absDx = Math.abs(dx);
    const absDy = Math.abs(dy);
    const elapsed = Math.max(1, performance.now() - startTime);
    const avgVelocity = absDx / elapsed; // px/ms

    let shouldTrigger = false;
    if (dx < 0) {
      // 1. 位移触发：达到阈值且横向明显占主导
      if (absDx >= threshold && absDx >= absDy * 1.25) {
        shouldTrigger = true;
      }
      // 2. 速度触发：快速横划，同时排除斜向滚动
      else if (
        absDx >= 36
        && absDx >= absDy * 1.25
        && (velocity <= -0.65 || avgVelocity >= 0.65)
      ) {
        shouldTrigger = true;
      }
    }

    if (progress) progress.value = 0;
    if (shouldTrigger) onSwipe();
  }

  function onPointerCancel(): void {
    tracking = false;
    pointerId = null;
    if (progress) progress.value = 0;
  }

  function detach(): void {
    if (!attachedTarget) return;
    attachedTarget.removeEventListener("pointerdown", onPointerDown);
    attachedTarget.removeEventListener("pointermove", onPointerMove);
    attachedTarget.removeEventListener("pointerup", onPointerUp);
    attachedTarget.removeEventListener("pointercancel", onPointerCancel);
    attachedTarget = null;
  }

  function attach(element: HTMLElement | null): void {
    if (attachedTarget === element) return;
    detach();
    if (!element) return;
    element.addEventListener("pointerdown", onPointerDown, { passive: true });
    element.addEventListener("pointermove", onPointerMove, { passive: true });
    element.addEventListener("pointerup", onPointerUp, { passive: true });
    element.addEventListener("pointercancel", onPointerCancel, { passive: true });
    attachedTarget = element;
  }

  onMounted(() => attach(target ? target.value : document.documentElement));

  if (target) {
    watch(target, (element) => attach(element));
  }

  onBeforeUnmount(() => {
    detach();
  });
}

/**
 * 跟手进度 ref 工厂（与 useSwipeNext 的 progress 配合使用）。
 * 返回一个 0~1 的 ref，表示当前左滑进度，用于UI视觉反馈。
 */
export function createSwipeProgress(): Ref<number> {
  return ref(0);
}
