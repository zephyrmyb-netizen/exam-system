import { createActor } from "xstate";
import { describe, expect, it } from "vitest";

import { practiceSessionMachine } from "../practiceSessionMachine";

function createSessionActor() {
  return createActor(practiceSessionMachine).start();
}

describe("practiceSessionMachine", () => {
  it("models the normal answer lifecycle without returning to an answered question", () => {
    const actor = createSessionActor();

    actor.send({ type: "START" });
    actor.send({ type: "QUESTION_READY" });
    actor.send({ type: "SUBMIT" });
    actor.send({ type: "ANSWER_CORRECT" });

    expect(actor.getSnapshot().value).toBe("correct");

    actor.send({ type: "NEXT" });
    expect(actor.getSnapshot().value).toBe("loading");

    actor.send({ type: "NO_MORE_QUESTIONS" });
    expect(actor.getSnapshot().value).toBe("completed");
  });

  it("keeps a failed submit in answer mode so the same answer can be retried", () => {
    const actor = createSessionActor();
    actor.send({ type: "START" });
    actor.send({ type: "QUESTION_READY" });
    actor.send({ type: "SUBMIT" });
    actor.send({ type: "SUBMIT_FAILED" });

    expect(actor.getSnapshot().value).toBe("answering");
  });
});
