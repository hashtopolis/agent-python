import unittest

from htpclient.helpers import strip_increment


class StripIncrement(unittest.TestCase):
    def test_removes_increment_with_equals_values(self):
        cmd = '#HL# -a 3 ?1 --increment --increment-min=1 --increment-max=6 -1 ?l?u?d?s'
        expected = '#HL# -a 3 ?1 -1 ?l?u?d?s'
        self.assertEqual(strip_increment(cmd), expected)

    def test_removes_increment_with_space_separated_values(self):
        cmd = '#HL# -a 3 ?1 --increment --increment-min 1 --increment-max 6 -1 ?l?u?d?s'
        expected = '#HL# -a 3 ?1 -1 ?l?u?d?s'
        self.assertEqual(strip_increment(cmd), expected)

    def test_removes_short_increment_flag(self):
        cmd = '#HL# -a 3 ?d?d?d?d -i'
        expected = '#HL# -a 3 ?d?d?d?d'
        self.assertEqual(strip_increment(cmd), expected)

    def test_leaves_command_without_increment_untouched(self):
        cmd = '#HL# -a 0 example.dict -r best64.rule'
        self.assertEqual(strip_increment(cmd), cmd)

    def test_does_not_touch_unrelated_flags(self):
        cmd = '#HL# -a 3 ?a?a?a --increment -w 3'
        expected = '#HL# -a 3 ?a?a?a -w 3'
        self.assertEqual(strip_increment(cmd), expected)

    def test_preserves_mask_with_runs_of_spaces(self):
        # The assembled benchmark command contains runs of spaces; the mask and
        # every other real token must survive (regression: a mask like ?d?d?d?d?d
        # was being dropped, leaving -a 3 with no mask).
        cmd = '-a 3 "/hashlists/11"  ?d?d?d?d?d   --hash-type=500  -o "/out"'
        result = strip_increment(cmd)
        self.assertIn('?d?d?d?d?d', result.split())
        self.assertIn('--hash-type=500', result.split())
        self.assertIn('-o', result.split())


if __name__ == '__main__':
    unittest.main()
