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

/**
 * Native file pickers can return to an already-mounted iOS/WKWebView with a
 * stale visual viewport. Reapply the browser viewport policy on resume, but do
 * not transform the application itself: scaling #app breaks fixed navigation
 * and can leave the document clipped to one side.
 */
export function installMobileViewportRecovery(): void {
  let recoveryInFlight = false;
  const restore = () => {
    if (recoveryInFlight) {
      return;
    }
    recoveryInFlight = true;
    applyMobileViewportPolicy();
    window.requestAnimationFrame(() => {
      applyMobileViewportPolicy();
    });
    window.setTimeout(() => {
      applyMobileViewportPolicy();
      recoveryInFlight = false;
    }, 80);
  };

  applyMobileViewportPolicy();
  window.addEventListener("pageshow", restore);
  window.addEventListener("focus", restore);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") restore();
  });
}
