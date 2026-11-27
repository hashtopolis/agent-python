import unittest
from htpclient.hashcat_cracker import (
    STREAM_CANDIDATE,
    STREAM_DIRECT,
    STREAM_KEYSPACE,
    keyspace_progress,
    stream_unit,
)

SKIP = 5000000
LENGTH = 100000


class TestStreamUnit(unittest.TestCase):
    def test_a_plain_task_runs_without_a_producer(self):
        self.assertEqual(stream_unit({}, False), STREAM_DIRECT)

    def test_a_preprocessor_emits_keyspace_units(self):
        self.assertEqual(stream_unit({'usePreprocessor': 1}, False), STREAM_KEYSPACE)
        self.assertEqual(stream_unit({'usePrince': True}, False), STREAM_KEYSPACE)

    def test_a_self_pipe_emits_candidates(self):
        self.assertEqual(stream_unit({}, True), STREAM_CANDIDATE)

    def test_a_preprocessor_wins_over_the_pipe_flag(self):
        # run_chunk prefers the preprocessor command, so the producer is the preprocessor
        self.assertEqual(stream_unit({'usePreprocessor': 1}, True), STREAM_KEYSPACE)
        self.assertEqual(stream_unit({'usePrince': True}, True), STREAM_KEYSPACE)


class TestKeyspaceProgress(unittest.TestCase):
    def test_direct_run_reports_curku_as_it_stands(self):
        # hashcat was given the chunk's --skip, so its restore point is already a task position
        self.assertEqual(keyspace_progress(SKIP, SKIP, LENGTH, STREAM_DIRECT), SKIP)
        self.assertEqual(keyspace_progress(SKIP + 2500, SKIP, LENGTH, STREAM_DIRECT), SKIP + 2500)
        self.assertEqual(keyspace_progress(0, SKIP, LENGTH, STREAM_DIRECT), 0)

    def test_keyspace_stream_on_hashcat_without_a_restore_point(self):
        # hashcat before 8.0 reported CURKU 0 for the whole of a piped run
        self.assertEqual(keyspace_progress(0, SKIP, LENGTH, STREAM_KEYSPACE), SKIP)

    def test_keyspace_stream_adds_the_chunk_offset(self):
        # the producer was given the window, so CURKU counts the stream from its start
        self.assertEqual(keyspace_progress(1200, SKIP, LENGTH, STREAM_KEYSPACE), SKIP + 1200)
        self.assertEqual(keyspace_progress(LENGTH, SKIP, LENGTH, STREAM_KEYSPACE), SKIP + LENGTH)

    def test_keyspace_stream_past_the_end_of_the_chunk_is_clamped(self):
        self.assertEqual(keyspace_progress(LENGTH * 7, SKIP, LENGTH, STREAM_KEYSPACE), SKIP + LENGTH)

    def test_candidate_stream_stays_at_the_chunk_start(self):
        # with two rules CURKU reaches the chunk's length half way through the chunk, so it cannot
        # be placed in the chunk; reporting the end would let the server skip the untried half
        for curku in (0, 1200, LENGTH, LENGTH * 2):
            with self.subTest(curku=curku):
                self.assertEqual(keyspace_progress(curku, SKIP, LENGTH, STREAM_CANDIDATE), SKIP)

    def test_first_chunk_of_a_task(self):
        self.assertEqual(keyspace_progress(0, 0, LENGTH, STREAM_KEYSPACE), 0)
        self.assertEqual(keyspace_progress(900, 0, LENGTH, STREAM_KEYSPACE), 900)


if __name__ == '__main__':
    unittest.main()
