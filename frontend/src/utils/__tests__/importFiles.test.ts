import { describe, expect, it } from "vitest";

import {
  ACCEPTED_IMPORT_FILE_TYPES,
  getFileExtension,
  isDocumentFile,
  isImageFile,
  isLegacyPpt,
  getFileKindLabel,
} from "../importFiles";

function file(name: string, type = ""): File {
  return new File(["x"], name, { type });
}

describe("import file helpers", () => {
  it("normalizes file extensions", () => {
    expect(getFileExtension("paper.DOCX")).toBe(".docx");
    expect(getFileExtension("archive")).toBe("");
  });

  it("classifies document, image, and legacy PowerPoint files", () => {
    expect(isDocumentFile(file("paper.docx"))).toBe(true);
    expect(isDocumentFile(file("slides.pptx"))).toBe(true);
    expect(isDocumentFile(file("exam.pdf"))).toBe(true);
    expect(isImageFile(file("shot.jpeg"))).toBe(true);
    expect(isImageFile(file("shot.webp"))).toBe(true);
    expect(isLegacyPpt(file("old.ppt"))).toBe(true);
  });

  it("returns user-facing labels for supported and legacy files", () => {
    expect(getFileKindLabel(file("paper.docx"))).toBe("Word 文档");
    expect(getFileKindLabel(file("slides.pptx"))).toBe("PPTX 演示文稿");
    expect(getFileKindLabel(file("exam.pdf"))).toBe("PDF 文档");
    expect(getFileKindLabel(file("shot.png"))).toBe("图片题目");
    expect(getFileKindLabel(file("old.ppt"))).toBe("旧版 PPT，不支持");
  });

  it("includes extensions and MIME types for mobile file pickers", () => {
    expect(ACCEPTED_IMPORT_FILE_TYPES.split(",")).toEqual([
      ".docx",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      ".pdf",
      "application/pdf",
      ".pptx",
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      ".png",
      "image/png",
      ".jpg",
      ".jpeg",
      "image/jpeg",
      ".webp",
      "image/webp",
    ]);
  });
});
