#!/usr/bin/env python3
"""
Security Check Script — 检查 Git 仓库是否误提交了密钥、敏感文件或构建产物。

可重复运行，适合集成到 CI（GitHub Actions / pre-commit hook）。

检查项
------
1. 禁止跟踪的路径：.env、数据库文件、构建产物、日志等。
2. 未被 .gitignore 忽略的敏感/生成文件：提醒先忽略或删除再提交。
3. 已跟踪文本文件中的密钥泄露：API Key、SECRET_KEY、GitHub Token、Bearer Token、sk- 密钥。
4. .env.example 中的空值或 <your-api-key> 占位符被视为安全，不报错。

用法
----
    python scripts/security_check.py

退出码：0 通过，1 失败（至少一项检查未通过）。
"""

import os
import re
import subprocess
import sys
from pathlib import Path


# ── 配置 ────────────────────────────────────────────────────────────────────

# 禁止在 git 跟踪中出现的路径/通配符模式（相对于仓库根目录）
FORBIDDEN_TRACKED_PATTERNS: list[str] = [
    # 环境变量文件
    ".env",
    "backend/.env",
    "frontend/.env",
    # 数据库文件
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.db-wal",
    "*.db-journal",
    # 构建产物及依赖
    "node_modules",
    "dist",
    # 用户上传
    "uploads",
    # Python 虚拟环境及缓存
    ".venv",
    "__pycache__",
    ".pytest_cache",
    # 日志
    "*.log",
]

# 密钥正则（扫描已跟踪文本文件）
#   key=value 模式：值不能为空，不能是占位符
SECRET_PATTERNS: list[tuple[str, str, str]] = [
    # (名称, 说明, 正则)
    (
        "OPENAI_API_KEY",
        "OpenAI API Key 已明文写入文件",
        r'OPENAI_API_KEY\s*=\s*(?!\s*(?:$|<your-api-key>|sk-proj-))(.+)',
    ),
    (
        "SECRET_KEY",
        "SECRET_KEY 已明文写入文件（非空/非占位符值）",
        r'SECRET_KEY\s*=\s*(?!\s*(?:$|change-this-secret))(.{8,})',
    ),
    (
        "GITHUB_TOKEN",
        "GitHub Token（github_pat_ / ghp_）已暴露",
        r'(?:github_pat_[a-zA-Z0-9_]{36,}|ghp_[a-zA-Z0-9]{36,})',
    ),
    (
        "BEARER_TOKEN",
        "Bearer Token 已暴露",
        r'Bearer\s+[A-Za-z0-9_\-]{20,}',
    ),
    (
        "SK_KEY",
        "疑似 OpenAI/第三方 sk- 密钥已暴露",
        r'sk-[A-Za-z0-9]{20,}',
    ),
]

# 允许的占位符值（.env.example 中安全的值）
PLACEHOLDER_VALUES: list[str] = [
    "",
    "<your-api-key>",
    "your-api-key-here",
    "sk-proj-...",
    "change-this-secret",
]

# 免检文件（相对路径匹配。这些文件不进行密钥扫描）
SKIP_SECRET_SCAN_PATTERNS: list[str] = [
    # 算法相关或测试固件中的假密钥
    "backend/tests/",
    "__pycache__/",
    ".pytest_cache/",
    "node_modules/",
    ".venv/",
    # 二进制/镜像/锁文件不扫描
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.svg",
    "*.ico",
    "*.woff",
    "*.woff2",
    "*.ttf",
    "*.eot",
    "*.ico",
    "*.pdf",
    "*.docx",
    "*.pptx",
    "*.xlsx",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.exe",
    "*.dll",
    "*.so",
    "*.dylib",
    "*.lock",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
]


# ── 工具函数 ────────────────────────────────────────────────────────────────


def run_git(args: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    """运行 git 命令，返回 CompletedProcess。"""
    return subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd or _repo_root(),
    )


def _repo_root() -> str:
    """返回 Git 仓库根目录的绝对路径。"""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("❌ 错误：当前目录不在 Git 仓库中。")
        sys.exit(1)
    return result.stdout.strip()


def matches_any_pattern(path: str, patterns: list[str]) -> bool:
    """检查 path 是否匹配 patterns 中的任意一个（支持通配符 *）。

    匹配规则：
    - *.ext → 后缀匹配
    - dir/  → 路径中包含该目录
    - 其他   → 路径末尾组件精确匹配（.env 只匹配名为 .env 的文件，
               不匹配 .env.example；backend/.env 匹配精确路径）
    """
    path_lower = path.lower()
    path_components = path_lower.replace("\\", "/").split("/")

    for pattern in patterns:
        pat_lower = pattern.lower().replace("\\", "/")

        # 处理 *.ext 通配符
        if pat_lower.startswith("*."):
            if path_lower.endswith(pat_lower[1:]):
                return True
        elif pat_lower.startswith("**/"):
            suffix = pat_lower[3:]
            if path_lower.endswith(suffix):
                return True
        elif pat_lower.endswith("/"):
            # 目录模式：检查路径中是否有该目录
            dir_name = pat_lower.rstrip("/")
            if dir_name in path_components:
                return True
        else:
            # 精确文件名匹配（路径末尾组件匹配）
            # 例如 ".env" 应匹配 "backend/.env" 但不匹配 "backend/.env.example"
            if "/" in pat_lower:
                # 跨目录的模式（如 "backend/.env"）：精确路径匹配
                if path_lower == pat_lower:
                    return True
            else:
                # 纯文件名模式：路径末尾组件精确匹配（不子串匹配）
                if path_components and path_components[-1] == pat_lower:
                    return True
    return False


def should_skip_secret_scan(file_path: str) -> bool:
    """判断文件是否应跳过密钥扫描（二进制、锁文件、测试固件等）。"""
    return matches_any_pattern(file_path, SKIP_SECRET_SCAN_PATTERNS)


def is_placeholder_value(value: str) -> bool:
    """判断值是否为安全的占位符。"""
    stripped = value.strip().strip('"').strip("'")
    if not stripped:
        return True
    return any(ph.lower() in stripped.lower() for ph in PLACEHOLDER_VALUES)


# ── 检查 1：禁止跟踪的路径 ───────────────────────────────────────────────────


def check_forbidden_tracked(repo_root: str) -> list[dict]:
    """
    检查是否有禁止的文件/目录被 Git 跟踪。
    返回错误列表 [{"path": ..., "reason": ...}, ...]
    """
    errors: list[dict] = []
    result = run_git(["ls-files"], cwd=repo_root)
    tracked_files = result.stdout.strip().split("\n")

    for tracked in tracked_files:
        if not tracked.strip():
            continue
        if matches_any_pattern(tracked, FORBIDDEN_TRACKED_PATTERNS):
            errors.append({
                "path": tracked,
                "reason": "禁止跟踪的文件类型/路径已被 Git 跟踪",
            })

    return errors


# ── 检查 2：未忽略的敏感/生成文件 ───────────────────────────────────────────


def check_forbidden_untracked(repo_root: str) -> list[dict]:
    """
    检查工作区中是否有未跟踪、且没有被 .gitignore 忽略的敏感/生成文件。

    已被 .gitignore 忽略的本地 .env / 数据库不报错；
    这里重点拦截“下一次 git add . 会误加入”的文件。
    """
    errors: list[dict] = []
    result = run_git(["ls-files", "--others", "--exclude-standard"], cwd=repo_root)
    untracked_files = result.stdout.strip().split("\n")

    for untracked in untracked_files:
        if not untracked.strip():
            continue
        if matches_any_pattern(untracked, FORBIDDEN_TRACKED_PATTERNS):
            errors.append({
                "path": untracked,
                "reason": "敏感/生成文件未被 .gitignore 忽略，存在误提交风险",
            })

    return errors


# ── 检查 2：密钥泄露扫描 ─────────────────────────────────────────────────────


def check_secrets_in_tracked(repo_root: str) -> list[dict]:
    """
    扫描已跟踪的文本文件，查找密钥泄露。
    返回错误列表 [{"path": ..., "reason": ..., "match": ...}, ...]
    """
    errors: list[dict] = []
    result = run_git(["ls-files"], cwd=repo_root)
    tracked_files = result.stdout.strip().split("\n")

    for tracked in tracked_files:
        if not tracked.strip():
            continue
        if should_skip_secret_scan(tracked):
            continue

        abs_path = os.path.join(repo_root, tracked)
        if not os.path.isfile(abs_path):
            continue

        # 仅扫描文本文件（跳过二进制）
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        # 如果是 .env.example 文件，做宽松检查
        is_env_example = tracked.endswith(".env.example")

        if is_env_example:
            # .env.example 中允许空值或占位符
            for name, desc, pattern in SECRET_PATTERNS:
                # 对 .env.example 使用更宽松的检查
                if name == "OPENAI_API_KEY":
                    # 找 OPENAI_API_KEY= 行，允许值为空/<your-api-key>占位符
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if re.match(r'^\s*#', line):
                            continue  # 跳过注释
                        m = re.match(r'OPENAI_API_KEY\s*=\s*(.*)', line)
                        if m:
                            val = m.group(1).strip()
                            if val and not is_placeholder_value(val):
                                errors.append({
                                    "path": tracked,
                                    "reason": f"{desc}（行 {line_num}）",
                                    "match": line.strip()[:80],
                                })
                elif name == "SECRET_KEY":
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if re.match(r'^\s*#', line):
                            continue
                        m = re.match(r'SECRET_KEY\s*=\s*(.*)', line)
                        if m:
                            val = m.group(1).strip()
                            if val and not is_placeholder_value(val) and len(val) > 8:
                                errors.append({
                                    "path": tracked,
                                    "reason": f"{desc}（行 {line_num}）",
                                    "match": line.strip()[:80],
                                })
            # 不扫描 .env.example 中的通用密钥模式
            continue

        # 普通文件：扫描所有密钥模式
        for line_num, line in enumerate(content.splitlines(), 1):
            line_stripped = line.strip()

            # 跳过注释行
            if line_stripped.startswith("#") or line_stripped.startswith("//") or line_stripped.startswith("/*"):
                continue

            for name, desc, pattern in SECRET_PATTERNS:
                matches = re.finditer(pattern, line)
                for m in matches:
                    matched_text = m.group(0)

                    # 额外确认不是占位符
                    if is_placeholder_value(matched_text):
                        continue

                    # 对于 sk- 模式，检查更严格（避免误报 sk-proj-... 示例）
                    if name == "SK_KEY" and is_env_example:
                        continue

                    errors.append({
                        "path": tracked,
                        "reason": f"{desc}（行 {line_num}）",
                        "match": matched_text[:80],
                    })

    return errors


# ── 主流程 ──────────────────────────────────────────────────────────────────


def _emoji_safe(text: str) -> str:
    """在 Windows 终端（GBK）下去掉 emoji，用纯文本替代。"""
    try:
        text.encode(sys.stdout.encoding or "utf-8")
        return text
    except (UnicodeEncodeError, UnicodeDecodeError):
        # 替换常见 emoji 为文本
        replacements = {
            "\U0001f510": "[SECURE]",   # 🔐
            "\U0001f4cb": "[CHECK-1]",  # 📋
            "\U0001f511": "[CHECK-2]",  # 🔑
            "\u274c": "[FAIL]",          # ❌
            "\u2705": "[PASS]",          # ✅
            "\u25cf": " - ",             # •
        }
        for emoji, alt in replacements.items():
            text = text.replace(emoji, alt)
        return text


def main() -> int:
    repo_root = _repo_root()
    repo_name = os.path.basename(repo_root)
    all_errors: list[dict] = []
    total_checks = 3
    passed_checks = 0

    def p(text: str, end: str = "\n") -> None:
        print(_emoji_safe(text), end=end)

    p(f"\U0001f510 安全检查：{repo_name}")
    p(f"   仓库路径：{repo_root}")
    p("")

    # ── 检查 1：禁止跟踪的路径 ────────────────────────────────────────────
    p("=" * 60)
    p("[CHECK-1] 检查 1/3：禁止跟踪的路径")
    p("=" * 60)
    errors = check_forbidden_tracked(repo_root)
    if errors:
        p(f"\u274c 失败：发现 {len(errors)} 个问题\n")
        for e in errors:
            p(f"     \u25cf {e['path']}")
            p(f"        原因：{e['reason']}")
        all_errors.extend(errors)
    else:
        p("  \u2705 通过：没有禁止的路径被跟踪")
        passed_checks += 1
    p("")

    # ── 检查 2：未忽略的敏感/生成文件 ────────────────────────────────────
    p("=" * 60)
    p("[CHECK-2] 检查 2/3：未忽略的敏感/生成文件")
    p("=" * 60)
    errors = check_forbidden_untracked(repo_root)
    if errors:
        p(f"\u274c 失败：发现 {len(errors)} 个问题\n")
        for e in errors:
            p(f"     \u25cf {e['path']}")
            p(f"        原因：{e['reason']}")
        all_errors.extend(errors)
    else:
        p("  \u2705 通过：没有可误提交的敏感/生成文件")
        passed_checks += 1
    p("")

    # ── 检查 3：密钥泄露扫描 ──────────────────────────────────────────────
    p("=" * 60)
    p("[CHECK-3] 检查 3/3：已跟踪文件密钥泄露扫描")
    p("=" * 60)
    errors = check_secrets_in_tracked(repo_root)
    if errors:
        p(f"\u274c 失败：发现 {len(errors)} 个问题\n")
        for e in errors:
            p(f"     \u25cf {e['path']} 行 {e['reason']}")
            p(f"        匹配内容：{e.get('match', 'N/A')}")
        all_errors.extend(errors)
    else:
        p("  \u2705 通过：未发现密钥泄露")
        passed_checks += 1
    p("")

    # ── 汇总 ──────────────────────────────────────────────────────────────
    p("=" * 60)
    if all_errors:
        p(f"\u274c 安全检查失败：共发现 {len(all_errors)} 个问题")
        p("")
        p("请修复以上问题后重新运行：")
        p("  1. 使用 `git rm --cached <file>` 停止跟踪禁止的文件")
        p("  2. 使用 `git update-index --assume-unchanged <file>` 忽略本地变更")
        p("  3. 或修改文件移除真实密钥，改用环境变量或占位符")
        p("")
        p("补充 .gitignore 规则后，请确保新文件不会再被跟踪：")
        p("   git rm -r --cached .  # 重新应用 .gitignore")
        p("   git add .")
        p("=" * 60)
        return 1
    else:
        p(f"\u2705 安全检查全部通过（{passed_checks}/{total_checks}）")
        p("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
