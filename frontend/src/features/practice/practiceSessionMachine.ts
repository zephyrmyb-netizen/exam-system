import { setup } from "xstate";

/**
 * The answer flow has a small but important lifecycle. Keeping it explicit
 * prevents a late fetch or auto-next timer from reviving a completed session.
 */
export type PracticeSessionPhase =
  | "idle"
  | "loading"
  | "answering"
  | "submitting"
  | "correct"
  | "wrong"
  | "error"
  | "completed";

export type PracticeSessionEvent =
  | { type: "START" }
  | { type: "QUESTION_READY" }
  | { type: "NO_MORE_QUESTIONS" }
  | { type: "LOAD_FAILED" }
  | { type: "SUBMIT" }
  | { type: "SUBMIT_FAILED" }
  | { type: "ANSWER_CORRECT" }
  | { type: "ANSWER_WRONG" }
  | { type: "NEXT" }
  | { type: "RETRY" };

export const practiceSessionMachine = setup({
  types: {
    events: {} as PracticeSessionEvent,
  },
}).createMachine({
  id: "practiceSession",
  initial: "idle",
  states: {
    idle: {
      on: { START: "loading" },
    },
    loading: {
      on: {
        QUESTION_READY: "answering",
        NO_MORE_QUESTIONS: "completed",
        LOAD_FAILED: "error",
      },
    },
    answering: {
      on: {
        SUBMIT: "submitting",
        NO_MORE_QUESTIONS: "completed",
      },
    },
    submitting: {
      on: {
        ANSWER_CORRECT: "correct",
        ANSWER_WRONG: "wrong",
        SUBMIT_FAILED: "answering",
      },
    },
    correct: {
      on: {
        NEXT: "loading",
        NO_MORE_QUESTIONS: "completed",
      },
    },
    wrong: {
      on: {
        NEXT: "loading",
        NO_MORE_QUESTIONS: "completed",
      },
    },
    error: {
      on: {
        RETRY: "loading",
        NO_MORE_QUESTIONS: "completed",
      },
    },
    completed: {
      on: {
        START: "loading",
      },
    },
  },
});
