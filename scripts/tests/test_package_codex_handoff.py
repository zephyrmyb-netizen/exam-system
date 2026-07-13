from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SCRIPT = REPO_ROOT / "scripts" / "package_codex_handoff.ps1"


class CodexHandoffPackageTests(unittest.TestCase):
    @classmethod
    def run_package_script(cls, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(cls.package_script),
                *arguments,
            ],
            cwd=cls.fixture_repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="xuexibao-handoff-test-"))
        cls.fixture_repo = cls.temp_dir / "repo"
        subprocess.run(
            ["git", "clone", "--quiet", "--no-hardlinks", str(REPO_ROOT), str(cls.fixture_repo)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        cls.package_script = cls.fixture_repo / "scripts" / "package_codex_handoff.ps1"
        fixture_test = cls.fixture_repo / "scripts" / "tests" / Path(__file__).name
        shutil.copy2(PACKAGE_SCRIPT, cls.package_script)
        shutil.copy2(Path(__file__).resolve(), fixture_test)
        subprocess.run(
            [
                "git",
                "-C",
                str(cls.fixture_repo),
                "add",
                "--",
                "scripts/package_codex_handoff.ps1",
                "scripts/tests/test_package_codex_handoff.py",
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        staged = subprocess.run(
            ["git", "-C", str(cls.fixture_repo), "diff", "--cached", "--quiet"]
        )
        if staged.returncode == 1:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(cls.fixture_repo),
                    "-c",
                    "user.name=Codex Test",
                    "-c",
                    "user.email=codex-test@example.invalid",
                    "commit",
                    "--quiet",
                    "-m",
                    "test fixture",
                ],
                check=True,
            )
        elif staged.returncode != 0:
            raise RuntimeError("could not inspect fixture repository index")

        cls.unrelated_untracked = (
            "docs/ops/active/2026-07-11-pencil-mcp-install.md",
            "docs/ops/active/2026-07-14-reference-ui-handoff-implementation.md",
            "frontend-preview.html",
        )
        for relative_path in cls.unrelated_untracked:
            path = cls.fixture_repo / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("intentionally excluded from handoff\n", encoding="utf-8")

        cls.output_dir = cls.temp_dir / "output"
        cls.build = cls.run_package_script("-OutputDirectory", str(cls.output_dir))
        cls.archives = sorted(cls.output_dir.glob("xuexibao-codex-handoff-*.zip"))

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def require_archive(self) -> Path:
        self.assertEqual(
            self.build.returncode,
            0,
            msg=f"packaging failed\nstdout:\n{self.build.stdout}\nstderr:\n{self.build.stderr}",
        )
        self.assertEqual(self.archives, self.archives[:1], "expected exactly one handoff archive")
        self.assertEqual(len(self.archives), 1, "expected exactly one handoff archive")
        return self.archives[0]

    def test_archive_uses_explicit_allowlist_and_required_root_metadata(self) -> None:
        archive = self.require_archive()
        expected_inclusions = {
            "HANDOFF_README.md",
            "SOURCE_TREE.txt",
            "SOURCE_REVISION.txt",
            "MANIFEST.sha256",
            "README.md",
            "docker-compose.yml",
            "exam-platform-ui/CODEX_HANDOFF.md",
            "exam-platform-ui/IMPLEMENTATION_MAP.md",
            "exam-platform-ui/pages/home.html",
            "frontend/.env.example",
            "frontend/package.json",
            "frontend/public/icon.svg",
            "frontend/src/router.ts",
            "backend/.env.example",
            "backend/main.py",
            "backend/migrations/versions/0001_initial_baseline.py",
            "backend/tests/api/test_courses_api.py",
            "docs/ops/INDEX.md",
            "scripts/package_codex_handoff.ps1",
            "scripts/tests/test_package_codex_handoff.py",
        }
        forbidden_exact = {
            "frontend-preview.html",
            "docs/ops/active/2026-07-11-pencil-mcp-install.md",
            "docs/ops/active/2026-07-14-reference-ui-handoff-implementation.md",
            "backend/.env",
            "backend/xuexibao.db",
            "acceptance-home-light.png",
        }

        with zipfile.ZipFile(archive) as handoff:
            names = {name.rstrip("/") for name in handoff.namelist() if not name.endswith("/")}

        self.assertTrue(expected_inclusions <= names, expected_inclusions - names)
        self.assertFalse(forbidden_exact & names, forbidden_exact & names)

        forbidden_segments = {
            ".git",
            ".venv",
            "venv",
            "cache",
            ".cache",
            "node_modules",
            "dist",
            "test-results",
            "uploads",
            "logs",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            ".mypy_cache",
            "artifacts",
        }
        for name in names:
            path = PurePosixPath(name)
            self.assertFalse(forbidden_segments & set(path.parts), name)
            self.assertFalse(name.lower().endswith((".db", ".sqlite", ".sqlite3", ".log")), name)
            self.assertFalse(path.name.startswith("acceptance-") and path.suffix.lower() == ".png", name)
            if path.name.startswith(".env"):
                self.assertEqual(path.name, ".env.example", name)

    def test_manifest_covers_every_file_and_matches_archive_bytes(self) -> None:
        archive = self.require_archive()
        with zipfile.ZipFile(archive) as handoff:
            file_names = {name for name in handoff.namelist() if not name.endswith("/")}
            manifest_lines = handoff.read("MANIFEST.sha256").decode("utf-8-sig").splitlines()
            manifest: dict[str, str] = {}
            for line in manifest_lines:
                digest, separator, name = line.partition("  ")
                self.assertEqual(separator, "  ", line)
                self.assertRegex(digest, r"^[0-9a-f]{64}$")
                manifest[name] = digest

            self.assertEqual(set(manifest), file_names - {"MANIFEST.sha256"})
            for name, expected_digest in manifest.items():
                actual_digest = hashlib.sha256(handoff.read(name)).hexdigest()
                self.assertEqual(actual_digest, expected_digest, name)

    def test_verify_mode_accepts_generated_archive(self) -> None:
        archive = self.require_archive()
        verification = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self.package_script),
                "-Verify",
                str(archive),
            ],
            cwd=self.fixture_repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(
            verification.returncode,
            0,
            msg=f"verification failed\nstdout:\n{verification.stdout}\nstderr:\n{verification.stderr}",
        )
        self.assertIn("verified", verification.stdout.lower())

    def test_verify_mode_rejects_unmanifested_file(self) -> None:
        archive = self.require_archive()
        tampered = self.temp_dir / "tampered.zip"
        shutil.copy2(archive, tampered)
        with zipfile.ZipFile(tampered, mode="a") as handoff:
            handoff.writestr("unexpected.txt", "not listed in the manifest")

        verification = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self.package_script),
                "-Verify",
                str(tampered),
            ],
            cwd=self.fixture_repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertNotEqual(verification.returncode, 0)

    def test_verify_mode_rejects_manifested_cache_directories(self) -> None:
        archive = self.require_archive()
        payload = b"cache data must never enter the handoff"

        for index, cache_name in enumerate(
            ("frontend/.cache/secret.txt", "frontend/cache/secret.txt")
        ):
            with self.subTest(cache_name=cache_name):
                tampered = self.temp_dir / f"tampered-cache-{index}.zip"
                with zipfile.ZipFile(archive) as source:
                    contents = {
                        name: source.read(name)
                        for name in source.namelist()
                        if not name.endswith("/")
                    }

                manifest = contents["MANIFEST.sha256"].decode("utf-8-sig").rstrip()
                digest = hashlib.sha256(payload).hexdigest()
                contents["MANIFEST.sha256"] = (
                    f"{manifest}\n{digest}  {cache_name}\n".encode("utf-8")
                )
                contents[cache_name] = payload

                with zipfile.ZipFile(
                    tampered, mode="w", compression=zipfile.ZIP_DEFLATED
                ) as handoff:
                    for name, data in contents.items():
                        handoff.writestr(name, data)

                verification = subprocess.run(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(self.package_script),
                        "-Verify",
                        str(tampered),
                    ],
                    cwd=self.fixture_repo,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                self.assertNotEqual(
                    verification.returncode,
                    0,
                    msg=f"verify accepted forbidden cache path: {cache_name}",
                )

    def test_package_allows_unrelated_untracked_files(self) -> None:
        for relative_path in self.unrelated_untracked:
            self.assertTrue((self.fixture_repo / relative_path).is_file(), relative_path)
        self.require_archive()

    def test_package_rejects_modified_tracked_source(self) -> None:
        target = self.fixture_repo / "README.md"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\nmodified after the declared revision\n")
            result = self.run_package_script(
                "-OutputDirectory", str(self.temp_dir / "dirty-tracked-output")
            )
        finally:
            target.write_bytes(original)

        self.assertNotEqual(
            result.returncode,
            0,
            msg="packaging accepted a modified tracked source file",
        )

    def test_package_rejects_untracked_source_in_allowlisted_directory(self) -> None:
        target = self.fixture_repo / "frontend" / "src" / "untracked-handoff-test.ts"
        target.write_text("export const mustNotBePackaged = true;\n", encoding="utf-8")
        try:
            result = self.run_package_script(
                "-OutputDirectory", str(self.temp_dir / "dirty-untracked-output")
            )
        finally:
            target.unlink()

        self.assertNotEqual(
            result.returncode,
            0,
            msg="packaging accepted untracked source from an allowlisted directory",
        )

    def test_verify_mode_rejects_malicious_directory_entries(self) -> None:
        archive = self.require_archive()

        for index, directory_name in enumerate(("../escape/", ".git/")):
            with self.subTest(directory_name=directory_name):
                tampered = self.temp_dir / f"tampered-directory-{index}.zip"
                shutil.copy2(archive, tampered)
                with zipfile.ZipFile(tampered, mode="a") as handoff:
                    handoff.writestr(directory_name, b"")

                verification = self.run_package_script("-Verify", str(tampered))
                self.assertNotEqual(
                    verification.returncode,
                    0,
                    msg=f"verify accepted malicious directory entry: {directory_name}",
                )


if __name__ == "__main__":
    unittest.main()
