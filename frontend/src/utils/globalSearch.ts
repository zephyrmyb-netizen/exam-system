export const GLOBAL_SEARCH_EVENT = "xuexibao-open-global-search";

export function openGlobalSearch(): void {
  window.dispatchEvent(new Event(GLOBAL_SEARCH_EVENT));
}
