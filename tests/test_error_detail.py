import subprocess
import unittest
from unittest import mock

from htpclient.helpers import format_error_detail
from htpclient.hashcat_cracker import HashcatCracker


class TestFormatErrorDetail(unittest.TestCase):
    def test_none_is_empty(self):
        self.assertEqual(format_error_detail(None), '')

    def test_empty_bytes_is_empty(self):
        self.assertEqual(format_error_detail(b''), '')

    def test_decodes_bytes(self):
        self.assertEqual(format_error_detail(b'plain error'), 'plain error')

    def test_strips_ansi_and_normalises_newlines(self):
        # A colour-wrapped two line message, CRLF terminated, trailing spaces.
        raw = b'\x1b[31mSeparator unmatched\x1b[0m\r\nsecond line  '
        self.assertEqual(format_error_detail(raw), 'Separator unmatched\nsecond line')

    def test_invalid_utf8_does_not_raise(self):
        # \xff is not valid UTF-8, so it decodes to U+FFFD (chr(0xfffd)).
        self.assertEqual(format_error_detail(b'bad \xff byte'), 'bad ' + chr(0xfffd) + ' byte')

    def test_keeps_the_tail_when_over_the_limit(self):
        # The real error is usually the last thing printed, so the tail is kept.
        out = ('noise\n' * 1000) + 'THE REAL ERROR'
        detail = format_error_detail(out, limit=40)
        self.assertEqual(len(detail), 40)
        self.assertTrue(detail.endswith('THE REAL ERROR'))

    def test_default_limit_is_2000(self):
        self.assertEqual(len(format_error_detail('x' * 3000)), 2000)


class TestKeyspaceErrorDetail(unittest.TestCase):
    """The keyspace measure failure path must send hashcat's own output to the
    server, not only the generic 'Keyspace measure failed!' text (issue 746)."""

    def _make_cracker(self):
        cracker = HashcatCracker.__new__(HashcatCracker)
        cracker.callPath = './hashcat.bin'
        cracker.cracker_path = '.'
        cracker.config = mock.MagicMock()
        cracker.config.get_value.return_value = 'devtoken'
        return cracker

    @mock.patch('htpclient.hashcat_cracker.sleep', return_value=None)
    @mock.patch('htpclient.hashcat_cracker.send_error')
    @mock.patch('htpclient.hashcat_cracker.update_files', return_value=' #HL# -a3 ?l?l?l?l ')
    @mock.patch('htpclient.hashcat_cracker.subprocess.check_output')
    def test_failure_propagates_detail(self, mock_check, mock_update, mock_send, mock_sleep):
        raw = b'\x1b[31mHashfile on line 1: Separator unmatched\x1b[0m\r\n'
        mock_check.side_effect = subprocess.CalledProcessError(255, 'cmd', output=raw)

        task = mock.MagicMock()
        task.get_task.return_value = {
            'attackcmd': '#HL# -a3 ?l?l?l?l',
            'hashlistAlias': '#HL#',
            'cmdpars': '',
            'taskId': 7,
        }
        chunk = mock.MagicMock()

        result = self._make_cracker().measure_keyspace(task, chunk)

        self.assertFalse(result)
        chunk.send_keyspace.assert_not_called()
        mock_send.assert_called_once()

        message, token, task_id, chunk_id = mock_send.call_args[0]
        self.assertIn('Keyspace measure failed!', message)
        self.assertIn('Separator unmatched', message)
        self.assertNotIn('\x1b', message)
        self.assertEqual(task_id, 7)
        self.assertIsNone(chunk_id)

    @mock.patch('htpclient.hashcat_cracker.sleep', return_value=None)
    @mock.patch('htpclient.hashcat_cracker.send_error')
    @mock.patch('htpclient.hashcat_cracker.update_files', return_value=' #HL# -a3 ?l?l?l?l ')
    @mock.patch('htpclient.hashcat_cracker.subprocess.check_output')
    def test_failure_without_output_sends_generic_message(self, mock_check, mock_update, mock_send, mock_sleep):
        # A crash that printed nothing must still send the generic message, with
        # no dangling separator from an empty detail.
        mock_check.side_effect = subprocess.CalledProcessError(255, 'cmd', output=b'')

        task = mock.MagicMock()
        task.get_task.return_value = {
            'attackcmd': '#HL# -a3 ?l?l?l?l',
            'hashlistAlias': '#HL#',
            'cmdpars': '',
            'taskId': 7,
        }

        self._make_cracker().measure_keyspace(task, mock.MagicMock())

        message = mock_send.call_args[0][0]
        self.assertEqual(message, 'Keyspace measure failed!')


if __name__ == '__main__':
    unittest.main()
