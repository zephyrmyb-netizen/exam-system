<template>
  <div class="import-capability-strip">
    <div class="import-capability">
      <span class="capability-label">当前支持</span>
      <strong>Word .docx / PDF .pdf / PPTX .pptx / PNG JPG WEBP</strong>
    </div>
    <div class="import-capability">
      <span class="capability-label">处理提示</span>
      <strong>文档 30-120 秒，图片 10-60 秒</strong>
    </div>
    <div class="import-capability import-capability--wide">
      <span class="capability-label">切换页面</span>
      <strong>解析不中断，回来可继续查看</strong>
    </div>
  </div>
</template>

<style scoped>
.import-capability-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-2);
}

.import-capability {
  display: grid;
  gap: 2px;
  min-height: 58px;
  padding: 10px 12px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background:
    linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(255, 255, 255, 0.88)),
    var(--surface);
}

.import-capability--wide {
  grid-column: 1 / -1;
}

.capability-label {
  color: var(--text-placeholder);
  font-size: 10px;
  font-weight: 800;
}

.import-capability strong {
  color: var(--text-main);
  font-size: var(--text-xs);
  line-height: 1.35;
}
</style>
