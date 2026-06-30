import { onBeforeUnmount, onMounted, ref, type Ref } from "vue";

interface UseSwipeNextOptions {
  /** 触发回调（一般传入下一题函数） */
  onSwipe: () => void;
  /** 横向位移阈值（px），默认 50（降低灵敏度门槛） */
  threshold?: number;
  /** 是否启用，传入 ref 控制启停（如仅在 result 显示时响应） */
  enabled?: Ref<boolean>;
  /** 跟手进度 ref（可选），0~1，用于UI反馈 */
  progress?: Ref<number>;
}

/**
 * 原生 pointer events 实现的"从右往左滑 -> 下一题"手势。
 *
 * 触发条件（满足任一即触发，让滑动更灵敏）：
 * 1. 位移触发：dx < 0 且 |dx| >= threshold 且 |dx| >= |dy| * 0.6
 *    （放宽纵向限制：允许横向位移是纵向的 1.67 倍以内，斜向滑动也能触发）
 * 2. 速度触发：dx < 0 且 |dx| >= 20 且速度 > 0.6 px/ms（快速划走）
 *
 * 同时通过 progress ref 实时输出滑动进度（0~1），用于跟手视觉反馈。
 */
export function useSwipeNext(options: UseSwipeNextOptions): void {
  const { onSwipe, threshold = 50, enabled, progress } = options;

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

  function onPointerDown(event: PointerEvent): void {
    if (!isEnabled()) return;
    // 仅主键 / 触摸
    if (event.button !== 0 && event.pointerType === "mouse") return;
    startX = event.clientX;
    startY = event.clientY;
    lastX = event.clientX;
    startTime = performance.now();
    lastTime = startTime;
    velocity = 0;
    tracking = true;
    if (progress) progress.value = 0;
  }

  function onPointerMove(event: PointerEvent): void {
    if (!tracking || !isEnabled()) return;
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
    if (dx < 0 && Math.abs(dx) >= Math.abs(dy) * 0.6) {
      if (progress) progress.value = Math.min(1, Math.abs(dx) / threshold);
    } else if (progress) {
      progress.value = 0;
    }
  }

  function onPointerUp(event: PointerEvent): void {
    if (!tracking) return;
    tracking = false;
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
      // 1. 位移触发：达到阈值且横向占主导（放宽到 0.6 倍）
      if (absDx >= threshold && absDx >= absDy * 0.6) {
        shouldTrigger = true;
      }
      // 2. 速度触发：快速划（位移≥20px，速度≥0.6px/ms）
      else if (absDx >= 20 && (velocity <= -0.6 || avgVelocity >= 0.6)) {
        shouldTrigger = true;
      }
    }

    if (progress) progress.value = 0;
    if (shouldTrigger) onSwipe();
  }

  function onPointerCancel(): void {
    tracking = false;
    if (progress) progress.value = 0;
  }

  onMounted(() => {
    window.addEventListener("pointerdown", onPointerDown, { passive: true });
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerup", onPointerUp, { passive: true });
    window.addEventListener("pointercancel", onPointerCancel, { passive: true });
  });

  onBeforeUnmount(() => {
    window.removeEventListener("pointerdown", onPointerDown);
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", onPointerUp);
    window.removeEventListener("pointercancel", onPointerCancel);
  });
}

/**
 * 跟手进度 ref 工厂（与 useSwipeNext 的 progress 配合使用）。
 * 返回一个 0~1 的 ref，表示当前左滑进度，用于UI视觉反馈。
 */
export function createSwipeProgress(): Ref<number> {
  return ref(0);
}
