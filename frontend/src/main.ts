import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import i18n from "./i18n";
import { installMobileViewportRecovery } from "./utils/viewport";
import "@fontsource-variable/noto-sans-sc/wght.css";
import "./styles/base.css";
import "./styles/transitions.css";
import "./styles/utilities.css";
import "./style.css";
import "./styles/ios26.css";

installMobileViewportRecovery();

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(i18n);
app.mount("#app");

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // PWA support is progressive; app usage should not depend on service worker registration.
    });
  });
} else if ("serviceWorker" in navigator) {
  // A production service worker may still own this origin when the same phone
  // opens the Vite server later. Remove it so development always loads the
  // current Vue modules instead of a previously cached screen.
  void navigator.serviceWorker.getRegistrations().then((registrations) =>
    Promise.all(registrations.map((registration) => registration.unregister())),
  );

  if ("caches" in window) {
    void caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key.startsWith("xuexibao-shell-")).map((key) => caches.delete(key))),
    );
  }
}
