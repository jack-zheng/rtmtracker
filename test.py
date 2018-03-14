import unittest
import transfer
import json
import xml.etree.ElementTree as ET

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
        
    def test_generate_rtm_table(self):
        expected_header = ['AC Title', 'Testlink Id', 'Comment']
        ret = transfer.generate_rtm_table()
        self.assertEqual(ret.tag, 'table')
        self.assertEqual(ret.get('id'), 'ret_info')

        # assert table header
        headers = []
        for sub in ret.iter('th'):
            headers.append(sub.text)

        self.assertEqual(len(headers), 3)
        for sub in expected_header:
            self.assertTrue(sub in headers)
    
    def test_append_row_data(self):
        """
        after append, table row count is as expected
        """
        tabele = transfer.generate_rtm_table()
        tr = ET.fromstring('<tr><td>123</td></tr>')
        ret = transfer.append_row_data(tabele, [tr, tr])
        tr_count = len(list(ret.iter('tr')))
        self.assertEqual(tr_count, 3)
            
if __name__ == '__main__':
    unittest.main()