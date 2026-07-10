export const ALLOWED_IMPORT_EXTENSIONS = [".docx", ".pdf", ".pptx", ".png", ".jpg", ".jpeg", ".webp"] as const;
export const UNSUPPORTED_LEGACY_EXTENSIONS = [".ppt"] as const;
export const ACCEPTED_IMPORT_FILE_TYPES = [
  ".doc",
  "application/msword",
  ".docx",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ".pdf",
  "application/pdf",
  ".ppt",
  "application/vnd.ms-powerpoint",
  ".pptx",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  ".png",
  "image/png",
  ".jpg",
  ".jpeg",
  "image/jpeg",
  ".webp",
  "image/webp",
  ".txt",
  "text/plain",
].join(",");

type FileLike = Pick<File, "name" | "size"> | { name?: string; size?: number } | null | undefined;

export function getFileExtension(fileName: string | null | undefined): string {
  const name = fileName || "";
  const dot = name.lastIndexOf(".");
  if (dot <= 0 || dot === name.length - 1) return "";
  return name.slice(dot).toLowerCase();
}

export function isImageFile(file: FileLike): boolean {
  return [".png", ".jpg", ".jpeg", ".webp"].includes(getFileExtension(file?.name));
}

export function isDocumentFile(file: FileLike): boolean {
  return [".docx", ".pdf", ".pptx"].includes(getFileExtension(file?.name));
}

export function isLegacyPpt(file: FileLike): boolean {
  return UNSUPPORTED_LEGACY_EXTENSIONS.includes(getFileExtension(file?.name) as ".ppt");
}

export function isAllowedImportFile(file: FileLike): boolean {
  return ALLOWED_IMPORT_EXTENSIONS.includes(getFileExtension(file?.name) as (typeof ALLOWED_IMPORT_EXTENSIONS)[number]);
}

export function getFileKindLabel(file: FileLike): string {
  const ext = getFileExtension(file?.name);
  if (ext === ".docx") return "Word 文档";
  if (ext === ".pdf") return "PDF 文档";
  if (ext === ".pptx") return "PPTX 演示文稿";
  if ([".png", ".jpg", ".jpeg", ".webp"].includes(ext)) return "图片题目";
  if (ext === ".ppt") return "旧版 PPT，不支持";
  return "未知格式";
}

export function formatImportFileSize(size: number | null | undefined): string {
  const value = Number(size || 0);
  if (value <= 0) return "";
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)}KB`;
  return `${(value / 1024 / 1024).toFixed(1)}MB`;
}

export function getUnsupportedImportMessage(fileName: string | null | undefined): string {
  const ext = getFileExtension(fileName);
  if (ext === ".doc") {
    return "已选择旧版 .doc 文件；当前 AI 解析请先在 Word/WPS 中另存为 .docx 后上传。";
  }
  if (ext === ".ppt") {
    return "暂不支持旧版 .ppt，请在 PowerPoint/WPS 中另存为 .pptx 后上传。";
  }
  if (ext === ".txt") {
    return "已选择 TXT 文件；当前 AI 文件解析请先转换为 .docx 后上传，或复制文本后使用 JSON 导入。";
  }
  return `不支持 ${ext || "未知"} 格式，目前可选择 Word、PDF、PPT、图片、TXT 文件；AI 直接解析支持 DOCX、PDF、PPTX、PNG、JPG、WEBP。`;
}
