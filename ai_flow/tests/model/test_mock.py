import unittest

from ai_flow.tests.model import bar
from ai_flow.tests.model import foo
from mock import patch


class TestTaskExecution(unittest.TestCase):

    @patch.object(foo, 'some_fn')
    def test_bar(self, mock_some_fn):
        mock_some_fn.return_value = 'test-val-1'
        tmp = bar.Bar()
        assert tmp.method_2() == 'test-val-1'
        mock_some_fn.return_value = 'test-val-2'
        assert tmp.method_2() == 'test-val-2'
