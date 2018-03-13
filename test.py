import unittest
import transfer
import json

class TestCase(unittest.TestCase):

    def setUp(self):
        pass
        
    def testHello(self):
        self.assertEqual('hello', 'hello')
        
    def test_convert_create_ret_to_html(self):
        objstr = '{"given": "as prov admin", "importance": "low",\
        "then": "multiple standard elements been updated, no user info elements updated",\
        "title": "tttt01", "when": "i update multiple standard elements"}'
        
        retstr = '{"additionalInfo": {"external_id": "123475190", "has_duplicate": "False", "id": "1857707",\
        "msg": "ok", "new_name": "", "status_ok": 1, "tcversion_id": "1857708", "version_number": 1},\
        "id": "1857707", "message": "Success!", "operation": "createTestCase", "status": "True"}'

        expectedstr = '<tr><td>tttt01</td><td>PLT#-123475190</td><td> </td></tr>'
        
        ret = transfer.convert_create_ret_to_html(json.loads(objstr), json.loads(retstr))
        self.assertEqual(ret, expectedstr)
        

if __name__ == '__main__':
    unittest.main()