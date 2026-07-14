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
 * stale visual viewport. Reapplying the viewport policy on resume prevents
 * the shell from being left scaled and clipped to one side of the screen.
 */
export function installMobileViewportRecovery(): void {
  const restore = () => {
    applyMobileViewportPolicy();
    window.requestAnimationFrame(applyMobileViewportPolicy);
    window.setTimeout(applyMobileViewportPolicy, 80);
  };

  applyMobileViewportPolicy();
  window.addEventListener("pageshow", restore);
  window.addEventListener("focus", restore);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") restore();
  });
  window.visualViewport?.addEventListener("resize", () => {
    if (window.visualViewport && window.visualViewport.scale > 1.01) restore();
  });
}
