import sys
import requests
from requests.auth import HTTPBasicAuth
import json
import xml.etree.ElementTree as ET
import re
import testlink

def main():
    # test id is: 233718819
    body = get_page_body(sys.argv[1])
    # print("---> %s \n" %body)
    formatted = format_body(body)
    # print("formatted ---> %s \n" %formatted)
    ac_objs = get_case_objs(formatted)
    #create_testlink_cases(ac_objs)

def test():
    body = get_page_body(233717240)
    # print("---> %s \n" %body)
    formatted = format_body(body)
    # print("formatted ---> %s \n" %formatted)
    ac_objs = get_case_objs(formatted)
    print("processed case count: %s" % len(ac_objs))
    # suite: 1856183, project: 5182, author: jzheng
    create_testlink_cases(ac_objs, 1856183, 5182, 'jzheng')
    print("process done !!")
    
def get_formatted_html(page_id):
    # test folder: 1857489, page: 233718819
    body = get_page_body(page_id)
    return format_body(body)


def get_page_body(pageid):
    '''
    send request to get page body, parse it and return xml content which contains ac info
    '''
    url = "https://confluence.successfactors.com/rest/api/content/{}".format(pageid)
    auth = HTTPBasicAuth('I306454', 'Lanmolei01241')
    querystring = {"expand": "body.storage"}
    resp = requests.get(url, auth=auth, params=querystring)
    return json.loads(resp.text).get('body').get('storage').get('value')

def format_body(body):
    '''
    body is in borken format and contains some invalide characters,
    in this method we format it and filter those characters
    '''
    _invalids = ['ri:', 'ac:', '&nbsp;']

    # fix format and filter invalid characters
    fixed = '<root>{}</root>'.format(body)
    for key in _invalids:
        fixed = fixed.replace(key, '')
    return fixed

def update_rtm_to_comfluence_page(original_content, append_content):
    """
    @params01: original confluence content
    @params02: table content need to be append
    """
    processed_content = ""
    
    if '<table>' in original_content:
        processed_content = re.sub(r'<table>.*<\/table>', append_content, original_content)
    else:
        processed_content = original_content + append_content
    return processed_content
    
def get_story_ac_at_collection(formatted):
    """
    return passed story, ac, at objects for later testing
    sample return:
    {
        "story":{as:xx, i want:xx, then:xx, jira:xx},
        "ac":[{given:xx, when:xx, then:xx, acid:xx}, ac02...],
        "at":[{title:xx, importance:xx, acid:xx}, at02...]
    }
    """
    _target_fields = ['title:', 'given:', 'when:', 'then:', 'importance:', 'jira:', 'as:', 'i want to:']
    
    story_obj = {}
    ac_objs = []
    at_objs = []
    
    root = ET.fromstring(formatted)
    for node in root.iter('plain-text-body'):
        ac_str = ET.tostring(node, encoding='unicode').lower()
        # filter multiple space and <tag>
        ac_str = re.sub(r' +', ' ', ac_str)
        ac_str = re.sub(r'<.+>', '', ac_str)
        
        line_list = ac_str.split('\n')
        parsed_list = list(filter(None, list(map(str.strip, line_list))))
        
        # if contains key word 'jira' - loop 1 else loop 2
        if 'jira:' in parsed_list:
            parse_story(parsed_list)
        else:
            parse_ac_at(parsed_list)

        ac_obj = {}
        for sub in _target_fields:
            if sub in parsed_list:
                    value = parsed_list[parsed_list.index(sub) + 1]
                    ac_obj[sub.replace(':', '')] = value
            
        ac_objs.append(ac_obj)
        
    # remove empty ac_obj
    ac_objs = [obj for obj in ac_objs if obj]
    # remove story obj
    ac_objs = [obj for obj in ac_objs if 'jira' not in obj]
    return ac_objs

def parse_story(str_list):
    """
    process passed string, return story dict
    """
    pass

def parse_ac_at(str_list):
    """
    process passed string, return ac, at list
    """
    pass
    
def convert_create_ret_to_html(obj, create_ret):
    """
    pass the create result as parameter, this method will parse it and 
    return the HTML formate content. case title from obj, case id from create result.
    e.g. give a result: 
    {"additionalInfo": {"external_id": "123475190",
    "has_duplicate": False,
    "id": "1857707",
    "msg": "ok",
    "new_name": "",
    "status_ok": 1,
    "tcversion_id": "1857708",
    "version_number": 1},
    "id": "1857707",
    "message": "Success!",
    "operation": "createTestCase",
    "status": True}
      
    obj:
    {"given": "as prov admin",
    "importance": "low",
    "then": "multiple standard elements been updated, no user info elements updated",
    "title": "tttt01",
    "when": "i update multiple standard elements"}
      
    return: 
    <tr>
       <td>tttt01</td>
       <td>PLT#-123475190</td>
       <td></td>
    </tr>
    """
    title_column = obj.get("title")
    id_column = "PLT#-" + create_ret.get("additionalInfo").get("external_id")
    
    # create XML tree and return XML tostring as result
    tr_node = ET.Element('tr')
    td1_node = ET.SubElement(tr_node, 'td')
    td1_node.text = title_column
    td2_node = ET.SubElement(tr_node, 'td')
    td2_node.text = id_column
    td3_node = ET.SubElement(tr_node, 'td')
    td3_node.text = ' '
    return ET.tostring(tr_node, encoding='unicode')
    
def generate_rtm_table():
    """
    return tbody HTML content
    """
    table_html = '''
    <table id="ret_info">
        <tbody>
            <tr>
                <th>AC Title</th>
                <th>Testlink Id</th>
                <th>Comment</th>
            </tr>
        </tbody>
    </table>'''
    return ET.fromstring(table_html)
    

def append_row_data(table, rows):
    """
    @param: table, XML's elementtree obj
    @param: row: XML obj convert from Testlink result
    this method will append converted row data to table 
    """
    tbody = table.getchildren()[0]
    for row in rows:
        tbody.append(row)
        
    return table
    
# suite: 1856183, project: 5182, author: jzheng
def create_testlink_cases(ac_objs, suite_id, project_id, author):
    # define the fields we need when create test case
    _case_fields = ['title', 'importance']
    # loop ac objs to create test cases
    tlc = _init_testlink_client()
    create_ret = []
    for ac in ac_objs:
        case_title = ac.get(_case_fields[0])
        cast_importance = get_importance_level(ac.get(_case_fields[1]))
        case_steps = construct_steps()
        result_ret = tlc.createTestCase(case_title, suite_id, project_id, author,\
                       "this case is created by python auto script",steps=case_steps,\
                       preconditions='put some pre-conditions here', importance=cast_importance, executiontype=2)
        create_ret.append(result_ret[0])
        
    return create_ret

        
def get_importance_level(importance_level):
    # define importance status dict
    _imp_status = {'low': 1, 'medium': 2, 'high': 3}
    # try to get status from status dict first
    # if no ret get, set import status as medium as default
    case_importance = _imp_status.get(importance_level)
    return case_importance if case_importance else 2


def construct_steps():
    """
    steps sample:
        [{'step_number' : 1, 'actions' : "action A" , 
        'expected_results' : "result A", 'execution_type' : 0},
        {'step_number' : 2, 'actions' : "action B" , 
        'expected_results' : "result B", 'execution_type' : 1},
        {'step_number' : 3, 'actions' : "action C" , 
        'expected_results' : "result C", 'execution_type' : 0}]
    """
    _steps = ['given', 'when', 'then']
    _step_attribute = ['step_number', 'actions', 'expected_results', 'execution_type']
    step_list = []
    one_step = {}
    # step_actions = "";
    # one_step[_step_attribute[0]] = 1
    # one_step[_step_attribute[1]] = step_actions
    # one_step[_step_attribute[2]] = ''
    # one_step[_step_attribute[3]] = 2
    # print('one_step: %s' % one_step)
    # step_list.append(one_step)
    return step_list
    
def construct_summary(ac_obj):
    """
    return summary, content is formated ac expression
    """
    _steps = ['given', 'when', 'then']
    content = "<p>" + _steps[0] + ":\n</p><p style='text-indent: 30px'>    " + ac_obj.get(_steps[0]) + "\n</p>"\
                  +"<p>" + _steps[1] + ":\n</p><p style='text-indent: 30px'>    " + ac_obj.get(_steps[1]) + "\n</p>"\
                  +"<p>" + _steps[2] + ":\n</p><p style='text-indent: 30px'>    " + ac_obj.get(_steps[2]) + "\n</p>"
    return content
 
def _init_testlink_client():
    key='c49d32b58989096d42282fd137ab58bc'
    url='http://10.3.153.50/testlink/lib/api/xmlrpc/v1/xmlrpc.php'
    return testlink.TestlinkAPIClient(url, key)

def list_cases_under_suite(suite_id):
    tlc = _init_testlink_client()
    return tlc.getTestCasesForTestSuite(testsuiteid=suite_id)
    

def list_test_suite_info(suite_id):
    tlc = _init_testlink_client()
    return tlc.getTestSuiteByID(testsuiteid=suite_id)
    
def get_test_case_eclipse_title(external_id):
	tlc = _init_testlink_client()
	case_detail = tlc.getTestCase(testcaseexternalid=external_id)[0]
	title_prefix = re.sub(r'\W', '', case_detail.get('full_tc_external_id'))
	title_subfix = re.sub(r'\W', '', case_detail.get('name').title())
	return title_prefix + title_subfix

if __name__ == '__main__':
    main()
