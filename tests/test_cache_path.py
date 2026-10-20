import unittest
from htpclient.hashcat_cracker import HashcatCracker, parse_version, select_cache_arg, version_supports_cache_path

# Versions as hashcat reports them: a release on its own, and a build made after one, which carries
# the commit count and hash. --cache-path arrived after 7.1.2 was released.
RELEASE_WITHOUT = "7.1.2"
BUILD_WITH = "7.1.2-629-g3b4a9ea09+"


class TestVersionSupportsCachePath(unittest.TestCase):
    def test_releases_without_the_option(self):
        self.assertFalse(version_supports_cache_path("7.1.2"))
        self.assertFalse(version_supports_cache_path("7.1.1"))
        self.assertFalse(version_supports_cache_path("7.0.0"))
        self.assertFalse(version_supports_cache_path("6.2.6"))

    def test_builds_on_that_release(self):
        # builds after 627 have the option
        self.assertTrue(version_supports_cache_path("7.1.2-628-g1a2b3c4d5"))
        self.assertTrue(version_supports_cache_path("7.1.2-629-g3b4a9ea09+"))
        self.assertTrue(version_supports_cache_path("7.1.2-658-gf975d8b"))
        self.assertTrue(version_supports_cache_path("7.1.2-1200-gabcdef1"))

    def test_builds_before_the_option_landed(self):
        # a self built snapshot from between the release and that commit has no such option, and
        # hashcat stops on one it does not know
        self.assertFalse(version_supports_cache_path("7.1.2-627-g6570a49f2"))
        self.assertFalse(version_supports_cache_path("7.1.2-626-gc84986904"))
        self.assertFalse(version_supports_cache_path("7.1.2-1-gdeadbee"))
        self.assertFalse(version_supports_cache_path("7.1.2-gnocount"))

    def test_later_releases(self):
        self.assertTrue(version_supports_cache_path("7.1.3"))
        self.assertTrue(version_supports_cache_path("7.2.0"))
        self.assertTrue(version_supports_cache_path("8.0.0"))
        self.assertTrue(version_supports_cache_path("10.0.0"))

    def test_unreadable_versions_are_treated_as_too_old(self):
        # an option hashcat does not know stops the run, so anything unclear has to say no
        self.assertFalse(version_supports_cache_path(""))
        self.assertFalse(version_supports_cache_path(None))
        self.assertFalse(version_supports_cache_path("latest"))
        self.assertFalse(version_supports_cache_path("unknown-build"))

    def test_whitespace_and_short_versions(self):
        self.assertTrue(version_supports_cache_path("  7.2.0\n"))
        self.assertFalse(version_supports_cache_path("7.1"))
        self.assertTrue(version_supports_cache_path("7.2"))


class TestSelectCacheArg(unittest.TestCase):
    def test_no_cache_path_configured(self):
        # the default: nothing configured, so the command line stays exactly as it was
        self.assertEqual(select_cache_arg('', BUILD_WITH), [])
        self.assertEqual(select_cache_arg(None, BUILD_WITH), [])

    def test_supported_cracker(self):
        self.assertEqual(
            select_cache_arg('/mnt/hccache', BUILD_WITH, isdir=lambda p: True),
            ['--cache-path="/mnt/hccache"']
        )

    def test_cracker_too_old_is_skipped(self):
        # 7.1.2 and older have no such option and abort on an unknown one
        with self.assertLogs(level='DEBUG') as logs:
            self.assertEqual(select_cache_arg('/mnt/hccache', RELEASE_WITHOUT, isdir=lambda p: True), [])
        self.assertEqual(len(logs.output), 1)
        self.assertIn('does not support', logs.output[0])
        self.assertIn('7.1.2', logs.output[0])

    def test_unreadable_version_is_skipped(self):
        self.assertEqual(select_cache_arg('/mnt/hccache', 'latest', isdir=lambda p: True), [])
        self.assertEqual(select_cache_arg('/mnt/hccache', '', isdir=lambda p: True), [])

    def test_missing_directory_is_skipped(self):
        # hashcat aborts when the cache directory it is handed does not exist, so we drop the option
        with self.assertLogs(level='DEBUG') as logs:
            self.assertEqual(select_cache_arg('/mnt/gone', BUILD_WITH, isdir=lambda p: False), [])
        self.assertEqual(len(logs.output), 1)
        self.assertIn('not a directory', logs.output[0])

    def test_path_with_space_stays_quoted(self):
        self.assertEqual(
            select_cache_arg('C:\\hashcat cache', BUILD_WITH, isdir=lambda p: True),
            ['--cache-path="C:\\hashcat cache"']
        )

    def test_path_with_double_quote_is_rejected(self):
        # the value is quoted, not escaped, when it lands in the shell command line
        with self.assertLogs(level='DEBUG') as logs:
            self.assertEqual(select_cache_arg('/mnt/a"b', BUILD_WITH, isdir=lambda p: True), [])
        self.assertEqual(len(logs.output), 1)
        self.assertIn('double quote', logs.output[0])


class TestParseVersion(unittest.TestCase):
    def test_release(self):
        self.assertEqual(parse_version("7.1.2"), (7, 1, 2))
        self.assertEqual(parse_version("  6.2.6\n"), (6, 2, 6))

    def test_build_drops_commit_hash(self):
        self.assertEqual(parse_version("7.1.2-629-g3b4a9ea09+"), (7, 1, 2, 629))
        self.assertEqual(parse_version("5.1.0-1618"), (5, 1, 0, 1618))

    def test_release_sorts_before_its_builds(self):
        self.assertLess(parse_version("7.1.2"), parse_version("7.1.2-1-gdeadbee"))
        self.assertLess(parse_version("7.1.2-1200-gabcdef1"), parse_version("7.1.3"))

    def test_unreadable(self):
        self.assertIsNone(parse_version(""))
        self.assertIsNone(parse_version(None))
        self.assertIsNone(parse_version("latest"))
        self.assertIsNone(parse_version("unknown-build"))
        self.assertIsNone(parse_version("7.1.2-gnocount"))


class TestOutfileFormat(unittest.TestCase):
    def outfile_format(self, version_string):
        cracker = HashcatCracker.__new__(HashcatCracker)  # skip __init__, which runs the binary
        cracker.version_string = version_string
        return cracker.get_outfile_format()

    def test_old_format(self):
        self.assertEqual(self.outfile_format("4.2.1"), "15")
        self.assertEqual(self.outfile_format("5.0.0-100-gabcdef1"), "15")
        self.assertEqual(self.outfile_format("5.1.0"), "15")
        self.assertEqual(self.outfile_format("5.1.0-1617-gabcdef1"), "15")

    def test_new_format(self):
        self.assertEqual(self.outfile_format("5.1.0-1618-gabcdef1"), "1,2,3,4")
        self.assertEqual(self.outfile_format("6.0.0"), "1,2,3,4")
        self.assertEqual(self.outfile_format("7.1.2-629-g3b4a9ea09+"), "1,2,3,4")

    def test_custom_version_assumes_new_format(self):
        self.assertEqual(self.outfile_format("custom"), "1,2,3,4")
        self.assertEqual(self.outfile_format(""), "1,2,3,4")


if __name__ == '__main__':
    unittest.main()
