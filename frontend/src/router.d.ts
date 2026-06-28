import "vue-router";

declare module "vue-router" {
  interface RouteMeta {
    requiresAuth?: boolean;
    guest?: boolean;
    title?: string;
    description?: string;
    navKey?: string;
    parent?: string;
    requiresPermission?: string;
  }
}
