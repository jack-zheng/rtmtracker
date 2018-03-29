import sys
import requests
from requests.auth import HTTPBasicAuth
import json
import xml.etree.ElementTree as ET
import re
import testlink

def main():
    pass

def test():
    # v2 test confluence page id: 235217044
    body = get_page_body(235217044)
    formatted = format_body(body)
    # print("formatted ---> %s \n" %formatted)
    return get_story_ac_at_collection(formatted)
    # print("processed case count: %s" % len(ac_objs))
    # suite: 1856183, project: 5182, author: jzheng
    # create_testlink_cases(ac_objs, 1856183, 5182, 'jzheng')
    # print("process done !!")
    

def get_page_body(pageid):
    '''
    send request to get page body, parse it and return xml content which contains ac info
    '''
    url = "https://confluence.successfactors.com/rest/api/content/{}".format(pageid)
    auth = HTTPBasicAuth('I306454', 'Lanmolei01241')
    querystring = {"expand": "body.storage"}
    resp = requests.get(url, auth=auth, params=querystring)
    
    # throw exception is request fail
    if resp.status_code != 200:
        mesg = "Send request fail, response show as: \n" + resp.text
        raise RuntimeError(mesg)
        
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
        "acs":[{given:xx, when:xx, then:xx, acid:xx}, ac02...],
        "ats":[{title:xx, importance:xx, acid:xx}, at02...]
    }
    """
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
            story_obj = parse_story(parsed_list)
        else:
            acid = len(ac_objs)
            ac_objs.append(parse_ac(parsed_list, acid))
            at_objs += (parse_at(parsed_list, acid))
            
    return {"story": story_obj, "acs": ac_objs, "ats": at_objs}

def parse_story(str_list):
    """
    process passed string, return story dictionary
    """
    _target_fields = ['then:', 'jira:', 'as:', 'i want to:']

    story = {}
    for sub in _target_fields:
        value = str_list[str_list.index(sub) + 1]
        story[sub.replace(':', '')] = value
    return story
    
def parse_ac(str_list, acid):
    """
    process string list passed in and return an ac obj
    """
    _target_fields = ['given:', 'when:', 'then:']

    ac = {"acid": acid}
    try:
        for sub in _target_fields:
            value = str_list[str_list.index(sub) + 1]
            ac[sub.replace(':', '')] = value
    except Exception as e:
        print(e)
        raise RuntimeError('Parse ac failed, ac show as below:\n' + str(str_list))
    return ac

    
def parse_at(str_list, acid):
    """
    process passed string, return at list
    """
    at_list = filter_at_collection(str_list)
    for sub in at_list:
        sub['acid'] = acid
    return at_list
    
def filter_at_collection(str_list):
    """
    input list and return in pair format
    e.g. input: ['acceptance criteria:',
                 'given:',
                 'ac01 given',
                 'when:',
                 'ac01 when',
                 'then:',
                 'ac01 then',
                 'acceptance test:',
                 'title:',
                 'at title 01',
                 'importance:',
                 'high',
                 'title:',
                 'at title 02']
         return [
                {'title':'at title 01',
                'importance': 'high'},
                {'title:': 'at title 02'}]
    """
    _target_fields = ['title:', 'importance:']
    sub = str_list[str_list.index(_target_fields[0]):]
    inds = [i for i, x in enumerate(sub) if x == 'title:']
    ac_list = []
    for i in range(0, len(inds)):
        if i == (len(inds) - 1):
            ac_obj = tuple_to_at_obj(tuple(sub[inds[i]:]))
        else:
            ac_obj = tuple_to_at_obj(tuple(sub[inds[i]:inds[i+1]]))
        ac_list.append(ac_obj)
        
    return ac_list
        
def tuple_to_at_obj(ac_tuple):
    """
    parse tuple to at object, if no importance is setting, set it as low as default
    
    input: ('title:', 'at title 01', 'importance:', 'high')
    return {'title': 'at title 01', 'importance': 'high'}
    
    input: ('title:', 'at title 01')
    return {'title': 'at title 01', 'importance': 'low'}
    """
    _target_fields = ['title:', 'importance:']
    at_obj = {}
    at_obj['title'] = ac_tuple[ac_tuple.index(_target_fields[0]) + 1]
    if _target_fields[1] in ac_tuple:
        at_obj['importance'] = ac_tuple[ac_tuple.index(_target_fields[1]) + 1]
    else: at_obj['importance'] = 'low'
    return at_obj
    
    
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
