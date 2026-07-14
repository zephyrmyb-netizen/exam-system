export const MOBILE_VIEWPORT_CONTENT =
  "width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover";

function viewportMeta(): HTMLMetaElement {
  let meta = document.querySelector<HTMLMetaElement>('meta[name="viewport"]');
  if (!meta) {
    meta = document.createElement("meta");
    meta.name = "viewport";
    document.head.append(meta);
  }
  return meta;
}

export function applyMobileViewportPolicy(): void {
  viewportMeta().content = MOBILE_VIEWPORT_CONTENT;
}

export function syncMobileViewportScale(): void {
  const scale = window.visualViewport?.scale ?? 1;
  const isZoomed = scale > 1.01;
  const root = document.documentElement;

  root.classList.toggle("viewport-scale-recovery", isZoomed);
  if (isZoomed) {
    root.style.setProperty("--viewport-recovery-scale", String(1 / scale));
  } else {
    root.style.removeProperty("--viewport-recovery-scale");
  }
}

/**
 * Native file pickers can return to an already-mounted iOS/WKWebView with a
 * stale visual viewport. Reapplying the viewport policy on resume prevents
 * the shell from being left scaled and clipped to one side of the screen.
 */
export function installMobileViewportRecovery(): void {
  let recoveryInFlight = false;
  const restore = () => {
    if (recoveryInFlight) {
      syncMobileViewportScale();
      return;
    }
    recoveryInFlight = true;
    applyMobileViewportPolicy();
    syncMobileViewportScale();
    window.requestAnimationFrame(() => {
      applyMobileViewportPolicy();
      syncMobileViewportScale();
    });
    window.setTimeout(() => {
      applyMobileViewportPolicy();
      syncMobileViewportScale();
      recoveryInFlight = false;
    }, 80);
  };

  applyMobileViewportPolicy();
  syncMobileViewportScale();
  window.addEventListener("pageshow", restore);
  window.addEventListener("focus", restore);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") restore();
  });
  window.visualViewport?.addEventListener("resize", () => {
    syncMobileViewportScale();
    if (window.visualViewport && window.visualViewport.scale > 1.01) restore();
  });
}
