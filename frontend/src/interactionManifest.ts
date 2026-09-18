export type InteractionRole = "anonymous" | "guest" | "student" | "admin";

export interface InteractionManifestEntry {
  routeName: string;
  roles: readonly InteractionRole[];
  actions: readonly string[];
}

// This is the release checklist for user-triggered flows. It is intentionally
// route-based so new routed surfaces cannot be added without an owner and a
// concrete set of user-visible outcomes.
export const interactionManifest: readonly InteractionManifestEntry[] = [
  { routeName: "login", roles: ["anonymous"], actions: ["login", "guest-login", "open-register"] },
  { routeName: "register", roles: ["anonymous"], actions: ["register", "open-login"] },
  {
    routeName: "home",
    roles: ["guest", "student", "admin"],
    actions: ["search", "open-course", "open-import", "open-practice", "share-course"],
  },
  {
    routeName: "courses",
    roles: ["guest", "student", "admin"],
    actions: ["filter", "create-course", "open-course", "share-course"],
  },
  {
    routeName: "course-detail",
    roles: ["guest", "student", "admin"],
    actions: ["practice", "import", "edit", "export", "publish", "delete", "share-course"],
  },
  {
    routeName: "shared-course",
    roles: ["guest", "student", "admin"],
    actions: ["preview-shared-course", "copy-shared-course"],
  },
  { routeName: "course-practice", roles: ["guest", "student", "admin"], actions: ["answer", "submit", "end-practice"] },
  {
    routeName: "public-library",
    roles: ["guest", "student", "admin"],
    actions: [
      "search-public-course",
      "open-public-course",
      "copy-public-course",
      "favorite-public-course",
      "report-public-course",
    ],
  },
  {
    routeName: "import",
    roles: ["guest", "student", "admin"],
    actions: ["select-file", "preview", "confirm-import", "manual-import"],
  },
  {
    routeName: "practice",
    roles: ["guest", "student", "admin"],
    actions: ["start-practice", "open-wrong", "open-due", "open-history"],
  },
  { routeName: "practice-wrong", roles: ["guest", "student", "admin"], actions: ["start-wrong-practice"] },
  { routeName: "practice-due", roles: ["guest", "student", "admin"], actions: ["start-due-practice"] },
  { routeName: "practice-history", roles: ["guest", "student", "admin"], actions: ["open-history-detail"] },
  {
    routeName: "exams",
    roles: ["guest", "student", "admin"],
    actions: ["refresh-exams", "create-exam", "open-exam", "refresh-my-exams"],
  },
  {
    routeName: "exam-create",
    roles: ["guest", "student", "admin"],
    actions: ["select-exam-question", "save-draft", "create-and-publish"],
  },
  {
    routeName: "exam-detail",
    roles: ["guest", "student", "admin"],
    actions: ["start-exam", "publish-own-draft", "open-leaderboard", "copy-exam-share-link", "open-exam-analytics"],
  },
  {
    routeName: "exam-share-link",
    roles: ["guest", "student", "admin"],
    actions: ["resolve-shared-exam", "retry-shared-exam"],
  },
  {
    routeName: "exam-take",
    roles: ["guest", "student", "admin"],
    actions: ["answer-exam", "navigate-exam", "submit-exam"],
  },
  {
    routeName: "exam-result",
    roles: ["guest", "student", "admin"],
    actions: ["view-leaderboard", "return-to-exams", "add-exam-wrong-answers"],
  },
  { routeName: "exam-leaderboard", roles: ["guest", "student", "admin"], actions: ["return-to-exam"] },
  {
    routeName: "exam-analytics",
    roles: ["guest", "student", "admin"],
    actions: ["refresh-exam-analytics", "return-to-exam"],
  },
  {
    routeName: "mine",
    roles: ["guest", "student", "admin"],
    actions: ["open-overview", "open-wrongbook", "open-bookmarks", "logout"],
  },
  {
    routeName: "wrongbook",
    roles: ["guest", "student", "admin"],
    actions: ["search-wrongbook", "remove-wrong-item", "practice-wrongbook"],
  },
  {
    routeName: "bookmarks",
    roles: ["guest", "student", "admin"],
    actions: ["filter-bookmarks", "open-bookmark", "remove-bookmark"],
  },
  { routeName: "chat", roles: ["guest", "student", "admin"], actions: ["send-chat", "retry-chat"] },
  {
    routeName: "study-overview",
    roles: ["guest", "student", "admin"],
    actions: ["start-due-review", "start-wrong-review", "start-practice", "save-study-plan"],
  },
  {
    routeName: "study-groups",
    roles: ["guest", "student", "admin"],
    actions: [
      "create-study-group",
      "join-study-group",
      "copy-invite-code",
      "view-study-group-resources",
      "share-group-course",
      "share-group-exam",
    ],
  },
  { routeName: "announcements", roles: ["guest", "student", "admin"], actions: ["read-announcement"] },
  {
    routeName: "help-feedback",
    roles: ["guest", "student", "admin"],
    actions: ["read-help", "submit-feedback", "submit-runtime-diagnostic"],
  },
  { routeName: "admin-dashboard", roles: ["admin"], actions: ["view-platform-stats", "open-user-management"] },
  { routeName: "admin-users", roles: ["admin"], actions: ["refresh-users", "change-user-role"] },
  {
    routeName: "admin-feedback",
    roles: ["admin"],
    actions: ["filter-feedback", "reply-feedback", "update-feedback-status"],
  },
  { routeName: "not-found", roles: ["anonymous", "guest", "student", "admin"], actions: ["return-home"] },
];
