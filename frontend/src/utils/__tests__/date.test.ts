import { describe, expect, it } from "vitest";

import { parseApiTimestamp } from "../date";

describe("parseApiTimestamp", () => {
  it("treats backend ISO timestamps without a timezone suffix as UTC", () => {
    expect(parseApiTimestamp("2026-07-14T02:00:00.000000"))
      .toBe(Date.parse("2026-07-14T02:00:00.000000Z"));
  });

  it.each([
    "2026-07-14T02:00:00.000Z",
    "2026-07-14T10:00:00.000+08:00",
    "2026-07-13T21:30:00.000-04:30",
  ])("preserves an explicit timezone in %s", (timestamp) => {
    expect(parseApiTimestamp(timestamp)).toBe(Date.parse(timestamp));
  });

  it.each([null, undefined, "", "not-a-timestamp", "2026-13-40T25:61:61"])(
    "rejects invalid API timestamp %s",
    (timestamp) => {
      expect(parseApiTimestamp(timestamp)).toBeNull();
    },
  );
});
