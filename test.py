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
        
    def test_update_rtm_to_comfluence_page_no_ret_in_page(self):
        """
        when there is no table in page, test method will append table 
        to the page content directly
        """
        ret = transfer.update_rtm_to_comfluence_page("fake content ", "append content")
        self.assertEqual(ret, "fake content append content")
        
    def test_update_rtm_to_comfluence_page_get_ret_in_page(self):
        """
        when there is table in page, test method will replace original table with 
        the new one
        """
        append_content = "<table>234</table>"
        ret = transfer.update_rtm_to_comfluence_page("fake<table>123</table>content", append_content)
        self.assertEqual(ret, "fake<table>234</table>content")
        
    def test_construct_steps(self):
        """
        by default now, there will be no steps in testlink, we store steps detail into script(BBM or Qray)
        """
        ret = transfer.construct_steps()
        self.assertEqual([], ret)
        
    def test_construct_summary(self):
        """
        it's hard to test this content format method, we simply test the return will contains 
        key words like: given, when, then
        """
        fake_ac = json.loads('{"given": "as prov admin",\
        "then": "multiple standard element been added, multiple user info elements been updated",\
        "title": "multiple standard elements added + multiple user info elements updated",\
        "when": "i add multiple standard elements and update multiple user info elements"}')
        ret = transfer.construct_summary(fake_ac)
        # assert result contains both fake_ac's key and value
        keys = ['given', 'when', 'then']
        for sub in keys:
            self.assertTrue(sub in ret)
        
        for sub in keys:
            self.assertTrue(fake_ac.get(sub) in ret)
            
        self.assertTrue('title' not in ret)
        
    def test_get_story_ac_at_collection(self):
        """
        read prepared txt file content as formatted input
        """
        expected_story = {"jira": "PLT-68861", "as": "story as", "i want to": "story i want", "then": "story then"}
        
        expected_ac = [{"given": "ac01 given", "when": "ac01 when", "then": "ac01 then", "acid": "1"}, {"given": "ac02 given", "when": "ac02 when", "then": "ac02 then", "acid": "2"}]
        
        expected_at = [{"title": "at title 01", "importance": "High", "acid": "1"}, {"title": "at title 02", "acid": "1"}, {"title": "at title 03", "importance": "High", "acid": "2"}]
        
        with open('./test_data/formatted.txt') as file:
            formatted = file.read()
        ret = transfer.get_story_ac_at_collection(formatted)
        self.assertEqual(len(set(ret.get('story')) & set(expected_story)), 4)
        for sub in expected_ac:
            self.assertTrue(sub in ret.get('ac'))
            
        for sub in expected_at:
            self.assertTrue(sub in ret.get('at'))
        
if __name__ == '__main__':
    unittest.main()