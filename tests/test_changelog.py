import os
import subprocess
import tempfile
import unittest

from changelog_gen import classify_commit, generate_changelog, get_latest_tag


class TestChangelogGenerator(unittest.TestCase):
    def test_classify_conventional_commits(self):
        self.assertEqual(
            classify_commit("feat(auth): add OAuth2 PKCE flow"),
            ("Added", "**auth**: add OAuth2 PKCE flow"),
        )
        self.assertEqual(
            classify_commit("fix(parser): handle empty tag list"),
            ("Fixed", "**parser**: handle empty tag list"),
        )
        self.assertEqual(
            classify_commit("refactor(cli): simplify argument parsing"),
            ("Changed", "**cli**: simplify argument parsing"),
        )
        self.assertEqual(
            classify_commit("revert: drop legacy v1 endpoint"),
            ("Removed", "drop legacy v1 endpoint"),
        )

    def test_classify_breaking_and_freeform_commits(self):
        cat, entry = classify_commit("feat(api)!: require bearer token")
        self.assertEqual(cat, "Added")
        self.assertIn("**BREAKING**", entry)

        self.assertEqual(classify_commit("Add dark mode toggle")[0], "Added")
        self.assertEqual(classify_commit("Fix race condition in worker")[0], "Fixed")
        self.assertEqual(classify_commit("Remove deprecated v0 config")[0], "Removed")
        self.assertEqual(classify_commit("Update dependencies for release")[0], "Changed")

    def test_end_to_end_git_repo_since_last_tag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            def git(*args):
                subprocess.run(
                    ["git", "-C", tmpdir] + list(args),
                    check=True,
                    capture_output=True,
                    text=True,
                )

            git("init")
            git("config", "user.name", "Prince Jain")
            git("config", "user.email", "princejain756@gmail.com")

            f1 = os.path.join(tmpdir, "app.txt")
            with open(f1, "w", encoding="utf-8") as fh:
                fh.write("v0.1.0\n")
            git("add", "app.txt")
            git("commit", "-m", "feat: initial release")
            git("tag", "v0.1.0")

            with open(f1, "a", encoding="utf-8") as fh:
                fh.write("feature 1\n")
            git("add", "app.txt")
            git("commit", "-m", "feat(core): add tag range detector")

            with open(f1, "a", encoding="utf-8") as fh:
                fh.write("bugfix 1\n")
            git("add", "app.txt")
            git("commit", "-m", "fix(parser): resolve newline splitting bug")

            with open(f1, "a", encoding="utf-8") as fh:
                fh.write("cleanup\n")
            git("add", "app.txt")
            git("commit", "-m", "Remove unused legacy helper")

            with open(f1, "a", encoding="utf-8") as fh:
                fh.write("perf\n")
            git("add", "app.txt")
            git("commit", "-m", "perf: speed up git log parsing")

            self.assertEqual(get_latest_tag(tmpdir), "v0.1.0")
            md = generate_changelog(
                repo_path=tmpdir,
                version_label="0.2.0",
                release_date="2026-11-08",
            )
            self.assertIn("## [0.2.0] - 2026-11-08", md)
            self.assertIn("_Changes since `v0.1.0`_", md)
            self.assertIn("### Added\n- **core**: add tag range detector", md)
            self.assertIn("### Fixed\n- **parser**: resolve newline splitting bug", md)
            self.assertIn("### Changed\n- speed up git log parsing", md)
            self.assertIn("### Removed\n- Remove unused legacy helper", md)
            self.assertNotIn("initial release", md)


if __name__ == "__main__":
    unittest.main()
