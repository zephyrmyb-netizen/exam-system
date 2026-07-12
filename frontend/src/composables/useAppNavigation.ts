import { useRoute, useRouter, type RouteLocationRaw } from "vue-router";

const NAVIGATION_SOURCES = new Set(["home", "mine", "courses", "public-library", "practice", "import"]);
type NavigationSource = "home" | "mine" | "courses" | "public-library" | "practice" | "import";

function isNavigationSource(value: unknown): value is NavigationSource {
  return typeof value === "string" && NAVIGATION_SOURCES.has(value);
}

function addSource(target: RouteLocationRaw, source: NavigationSource): RouteLocationRaw {
  if (typeof target === "string") {
    return { path: target, query: { from: source } };
  }

  return {
    ...target,
    query: {
      ...(typeof target === "object" && "query" in target && target.query ? target.query : {}),
      from: source,
    },
  } as RouteLocationRaw;
}

export function useAppNavigation() {
  const router = useRouter();
  const route = useRoute();

  function replaceTo(target: RouteLocationRaw) {
    return router.replace(target);
  }

  function replaceWithSource(target: RouteLocationRaw, source: NavigationSource | string) {
    return router.replace(isNavigationSource(source) ? addSource(target, source) : target);
  }

  function returnToSource(fallback: RouteLocationRaw) {
    const from = route.query.from;
    return router.replace(isNavigationSource(from) ? { name: from } : fallback);
  }

  return { replaceTo, replaceWithSource, returnToSource };
}
