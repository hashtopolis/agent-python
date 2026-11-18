import unittest
from htpclient.hashcat_cracker import keyspace_progress

SKIP = 5000000
LENGTH = 100000


class TestKeyspaceProgress(unittest.TestCase):
    def test_direct_run_reports_curku_as_it_stands(self):
        # hashcat was given the chunk's --skip, so its restore point is already a task position
        self.assertEqual(keyspace_progress(SKIP, SKIP, LENGTH, False), SKIP)
        self.assertEqual(keyspace_progress(SKIP + 2500, SKIP, LENGTH, False), SKIP + 2500)
        self.assertEqual(keyspace_progress(0, SKIP, LENGTH, False), 0)

    def test_piped_run_on_hashcat_without_a_restore_point(self):
        # hashcat before 8.0 reported CURKU 0 for the whole of a piped run
        self.assertEqual(keyspace_progress(0, SKIP, LENGTH, True), SKIP)

    def test_piped_run_adds_the_chunk_offset(self):
        # the producer was given the window, so CURKU counts the stream from its start
        self.assertEqual(keyspace_progress(1200, SKIP, LENGTH, True), SKIP + 1200)
        self.assertEqual(keyspace_progress(LENGTH, SKIP, LENGTH, True), SKIP + LENGTH)

    def test_piped_run_past_the_end_of_the_chunk_is_clamped(self):
        # --slow-candidates counts candidates, so CURKU can outrun a chunk counted in base words
        self.assertEqual(keyspace_progress(LENGTH * 7, SKIP, LENGTH, True), SKIP + LENGTH)

    def test_first_chunk_of_a_task(self):
        self.assertEqual(keyspace_progress(0, 0, LENGTH, True), 0)
        self.assertEqual(keyspace_progress(900, 0, LENGTH, True), 900)


if __name__ == '__main__':
    unittest.main()
