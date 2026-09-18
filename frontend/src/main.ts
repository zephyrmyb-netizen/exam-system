import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import i18n from "./i18n";
import "./styles/base.css";
import "./styles/transitions.css";
import "./styles/utilities.css";
import "./style.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(i18n);
app.mount("#app");

const isBetaBuild = import.meta.env.VITE_APP_ENV === "beta";

function clearApplicationShellCache(): Promise<void> {
  const unregister =
    "serviceWorker" in navigator
      ? navigator.serviceWorker
          .getRegistrations()
          .then((registrations) => Promise.all(registrations.map((registration) => registration.unregister())))
      : Promise.resolve([]);

  const clearCaches =
    "caches" in window
      ? caches
          .keys()
          .then((keys) =>
            Promise.all(keys.filter((key) => key.startsWith("xuexibao-shell-")).map((key) => caches.delete(key))),
          )
      : Promise.resolve([]);

  return Promise.all([unregister, clearCaches]).then(() => undefined);
}

if (isBetaBuild && "serviceWorker" in navigator) {
  // Beta is deployed often. An offline shell can keep a mobile webview on an
  // old Vue bundle even after the server has been updated, so it is disabled
  // here until the release channel is stable.
  window.addEventListener("load", () => {
    void clearApplicationShellCache();
  });
} else if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js", { updateViaCache: "none" }).catch(() => {
      // PWA support is progressive; app usage should not depend on service worker registration.
    });
  });
} else if ("serviceWorker" in navigator) {
  // A production service worker may still own this origin when the same phone
  // opens the Vite server later. Remove it so development always loads the
  // current Vue modules instead of a previously cached screen.
  void clearApplicationShellCache();
}
