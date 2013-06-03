import contextlib

import mock
from unittest import TestCase

import hacheck.haupdown
import hacheck.spool

# can't use an actual mock.sentinel because it doesn't support string ops
sentinel_service_name = 'testing_service_name'


class TestCallable(TestCase):
    @contextlib.contextmanager
    def setup_wrapper(self, args=frozenset()):
        with mock.patch.object(hacheck, 'spool', return_value=(True, {})) as mock_spool,\
                mock.patch.object(hacheck.haupdown, 'print_s') as mock_print,\
                mock.patch('sys.argv', ['ignored', sentinel_service_name] + list(args)):
            yield mock_spool, mock_print

    def test_basic(self):
        with self.setup_wrapper() as (spooler, _):
            spooler.status.return_value = (True, {})
            hacheck.haupdown.main()
            spooler.configure.assert_called_once_with('/var/spool/hacheck', needs_write=True)

    def test_exit_codes(self):
        with self.setup_wrapper() as (spooler, mock_print):
            spooler.status.return_value = (True, {})
            self.assertEqual(0, hacheck.haupdown.main())
            mock_print.assert_any_call('UP\t%s', sentinel_service_name)
            spooler.status.return_value = (False, {'reason': 'irrelevant'})
            self.assertEqual(1, hacheck.haupdown.main())
            mock_print.assert_any_call('DOWN\t%s\t%s', sentinel_service_name, 'irrelevant')

    def test_up(self):
        with self.setup_wrapper() as (spooler, mock_print):
            hacheck.haupdown.up()
            spooler.up.assert_called_once_with(sentinel_service_name)
            self.assertEqual(mock_print.call_count, 0)

    def test_down(self):
        with self.setup_wrapper() as (spooler, mock_print):
            hacheck.haupdown.down()
            spooler.down.assert_called_once_with(sentinel_service_name, '')
            self.assertEqual(mock_print.call_count, 0)

    def test_down_with_reason(self):
        with self.setup_wrapper(['-r', 'something']) as (spooler, mock_print):
            hacheck.haupdown.down()
            spooler.down.assert_called_once_with(sentinel_service_name, 'something')
            self.assertEqual(mock_print.call_count, 0)

    def test_status(self):
        with self.setup_wrapper() as (spooler, mock_print):
            spooler.status.return_value = (True, {})
            hacheck.haupdown.status()
            spooler.status.assert_called_once_with(sentinel_service_name)
            mock_print.assert_called_once_with("UP\t%s", sentinel_service_name)

    def test_status_all(self):
        with self.setup_wrapper() as (spooler, mock_print):
            spooler.status_all_down.return_value = [(sentinel_service_name, {'service': sentinel_service_name, 'reason': ''})]
            self.assertEqual(hacheck.haupdown.status_all(), 0)
            mock_print.assert_called_once_with("DOWN\t%s\t%s", sentinel_service_name, mock.ANY)
