import { defineStore } from "pinia";

export const useUiStore = defineStore("ui", {
  state: () => ({
    sidebarOpen: false,
    globalLoading: false,
  }),
  actions: {
    toggleSidebar(): void {
      this.sidebarOpen = !this.sidebarOpen;
    },
    setSidebar(open: boolean): void {
      this.sidebarOpen = open;
    },
    setGlobalLoading(loading: boolean): void {
      this.globalLoading = loading;
    },
  },
});
