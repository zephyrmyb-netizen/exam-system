export function normalizeChatReply(text: string): string {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/`([^`\n]+)`/g, "$1")
    .replace(/^\s{0,3}#{1,6}\s+/gm, "")
    .replace(/(^|\s)-\s+/g, "$1\n• ")
    .replace(/[^\S\n]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderInlineMarkdown(text: string): string {
  return escapeHtml(text)
    .replace(/`([^`\n]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_\n]+)__/g, "<strong>$1</strong>");
}

function isListItem(line: string): boolean {
  return /^\s*(?:[-*]|\d+[.)])\s+/.test(line);
}

function stripListMarker(line: string): string {
  return line.replace(/^\s*(?:[-*]|\d+[.)])\s+/, "");
}

export function renderAssistantMarkdown(text: string): string {
  const normalized = text.replace(/\r\n/g, "\n").trim();
  if (!normalized) return "";

  const blocks: string[] = [];
  const paragraphLines: string[] = [];
  const listItems: string[] = [];

  function flushParagraph(): void {
    if (paragraphLines.length === 0) return;
    blocks.push(`<p>${paragraphLines.map(renderInlineMarkdown).join("<br>")}</p>`);
    paragraphLines.length = 0;
  }

  function flushList(): void {
    if (listItems.length === 0) return;
    blocks.push(`<ul>${listItems.map((item) => `<li>${renderInlineMarkdown(item)}</li>`).join("")}</ul>`);
    listItems.length = 0;
  }

  for (const line of normalized.split("\n")) {
    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    if (isListItem(line)) {
      flushParagraph();
      listItems.push(stripListMarker(line));
      continue;
    }

    flushList();
    paragraphLines.push(line);
  }

  flushParagraph();
  flushList();

  return blocks.join("");
}
