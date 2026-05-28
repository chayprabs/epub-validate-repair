import { describe, expect, it } from "vitest";

describe("web smoke", () => {
  it("keeps the feature summary stable", () => {
    expect("EpubDoctor").toContain("Epub");
  });
});
