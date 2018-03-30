import unittest
from unittest import mock
from mocktest import func1, func2
from mocktest import mktest as mc

class TestCase(unittest.TestCase):
    
    def testHello(self):
        self.assertEqual('hello', 'hello')
        
    @mock.patch('mocktest.func1')
    def test_func2(self, mock_func1):
        mock_func1.return_value = 0
        self.assertEqual(func2(5), 25)
        mock_func1.return_value = 10
        self.assertEqual(func2(-5), -15)
        
    def test_method(self):
        m = mc()
        self.assertEqual(m.method(), '12')
        
    @mock.patch('mocktest.mktest.method')
    def test_patch_method(self, mock_method):
        mock_method.return_value = '20'
        c = mc()
        self.assertEqual(c.method(), '20')
        

if __name__ == '__main__':
    unittest.main()