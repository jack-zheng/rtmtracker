import sys
import requests
from requests.auth import HTTPBasicAuth
import json
import xml.etree.ElementTree as ET
import re
import testlink

def main(pageid, folderid, projectid, author):
    # v2 test confluence page id: 235217044
    body = get_page_body(pageid)
    formatted = format_body(body)
    # print("formatted ---> %s \n" %formatted)
    ret = get_story_ac_at_collection(formatted)
    ats = ret.get('ats')
    acs = ret.get('acs')
    story = ret.get('story')
    create_ret = create_test_cases(ats, acs, story, folderid, projectid, author)
    print("----------------------> Test cases has been created in Testlink <----------------------")
    
    rows = generate_table_rows(ats, create_ret)
    table = generate_rtm_table()
    table_context = append_row_data(table, rows)
    body_context = update_rtm_to_comfluence_page(body, table_context)
    payload = prepare_update_payload(pageid, body_context)
    resp = update_confluence_page_body_api(pageid, payload)
    print("----------------------> update confluence status: %s <----------------------" % resp.status_code)
    # suite: 1857489(confluence transfer), project: 5182(platform), author: jzheng
    # create_testlink_cases(ac_objs, 1857489, 5182, 'jzheng')

    
def prepare_update_payload(pageid, update_content):
    resp = get_confluence_page_detail(pageid, "body.storage,version")
    payload_sample = '{"version": {"number": 0}, "id": "id_sample", "title": "title_sample","type": "page","body": {"storage": {"value": "value_sample","representation": "storage"}}}'
    payload_json = json.loads(payload_sample)
    
    # get fields need to be update
    resp_json = json.loads(resp.text)
    version_num = resp_json.get('version').get('number')
    id = resp_json.get('id')
    title = resp_json.get('title')
    
    # update payload content
    payload_json.get('version')['number'] = version_num + 1
    payload_json['id'] = id
    payload_json['title'] = title
    payload_json.get('body').get('storage')['value'] = update_content
    return json.dumps(payload_json)
    
def update_confluence_page_body_api(pageid, payload):
    url = "https://confluence.successfactors.com/rest/api/content/{}".format(pageid)
    auth = HTTPBasicAuth('I306454', 'Lanmolei01241')
    headers = {'Content-Type': "application/json"}
    resp = requests.request("PUT", url, auth=auth, data=payload, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError("Update confluence page failed, text: " + resp.text)
    return resp

def get_confluence_page_detail(pageid, fields):
    url = "https://confluence.successfactors.com/rest/api/content/{}".format(pageid)
    auth = HTTPBasicAuth('I306454', 'Lanmolei01241')
    querystring = {"expand": fields}
    resp = requests.get(url, auth=auth, params=querystring)
    
    # throw exception is request fail
    if resp.status_code != 200:
        mesg = "Send request fail, response show as: \n" + resp.text
        raise RuntimeError(mesg)
    return resp
        
def get_page_body(pageid):
    '''
    send request to get page body, parse it and return xml content which contains ac info
    '''
    resp = get_confluence_page_detail(pageid, "body.storage")
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
    
    
def generate_rtm_table():
    """
    return tbody HTML content
    """
    table_html = '''
    <table id="ret_info">
        <tbody>
            <tr>
                <th>AT Title</th>
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
    
    return string type table content
    """
    tbody = table.getchildren()[0]
    for row in rows:
        tbody.append(row)
        
    return ET.tostring(table, 'unicode')

    
def generate_table_rows(ats, create_rets):
    rows = []
    for ret in create_rets:
        atid  = ret.get('atid')
        if atid is None:
            raise RuntimeError("atid attribute in create result should not be none, rets: " + str(create_rets))
        filters = [at for at in ats if at.get('atid') == atid]
        if not filters:
            raise RuntimeError("There is no match at, atid = " + atid + ", ats: " + str(ats))
        row = convert_create_ret_to_html(filters[0], ret)
        rows.append(row)
    return rows
    
    
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
    return tr_node
    
    
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
            at_objs += (parse_at(parsed_list, acid, len(at_objs)))
            
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

    
def parse_at(str_list, acid, start):
    """
    process passed string, return at list
    """
    at_list = filter_at_collection(str_list)
    for index, sub in enumerate(at_list):
        sub['acid'] = acid
        sub['atid'] = index + start
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
    
    
def create_single_test_case(at, ac, story, suite_id, project_id, author):
    """
    @params01 at: which contains test case id and importance
    @params02 ac: which contains test case summary
    @params03 suite_id: locate of testlink folder
    @params04 project_id: locate of testlink folder
    @params05 author: the creator of test case
    
    return:
    {'additionalInfo': {'external_id': '123475531',
    'has_duplicate': False,
    'id': '1868121',
    'msg': 'ok',
    'new_name': '',
    'status_ok': 1,
    'tcversion_id': '1868122',
    'version_number': 1},
    'id': '1868121',
    'message': 'Success!',
    'operation': 'createTestCase',
    'status': True}
    """
    tlc = _init_testlink_client()
    print('processed at: %s' % at)
    case_title = at.get('title')
    case_importance = at.get('importance')
    importance_leve = get_importance_level(case_importance)
    print('importance level: %s' % importance_leve)
    case_summary = construct_summary(ac, story)
    result_ret = tlc.createTestCase(case_title, suite_id, project_id, author,\
                       case_summary,steps=[], preconditions='has not comment any step', \
                       importance=importance_leve, executiontype=2)
                       
    # result_ret is a list contains 1 ret, we return the ret directly
    result_ret[0]['atid'] = at.get('atid')
    return result_ret[0]

def create_test_cases(ats, acs, story, suite_id, project_id, author):
    """
    @params01: acceptance criteria collection
    @params02: acceptance tests collection
    we parse the input, find our the ac match with at, and parse ac, at to create_single_test_case method 
    to create all test cases
    """
    test_case_info = []
    for at in ats:
        acid = at.get('acid')
        if acid is None:
            raise RuntimeError("acid should not be null, ats: " + str(ats))
        mapped_ac = {}
        for ac in acs:
            if ac.get('acid') == acid:
                mapped_ac = ac
                break
        if not mapped_ac:
            raise RuntimeError("Can't find matched ac, acs: " + str(acs) + " ats: " + str(ats))
        ret = create_single_test_case(at, ac, story, suite_id, project_id, author)
        test_case_info.append(ret)
    return test_case_info
    
        
def get_importance_level(importance_level):
    # define importance status dict
    _imp_status = {'low': 1, 'medium': 2, 'high': 3}
    # try to get status from status dict first
    # if no ret get, set import status as medium as default
    case_importance = _imp_status.get(importance_level)
    return case_importance if case_importance else 1


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
    
def construct_summary(ac_obj, story):
    """
    return summary, content is formated ac expression
    """
    _steps = ['given', 'when', 'then']
    content = "<p> Jira Id: " + story.get('jira') + "\n</p>"\
                  +"<p>" + _steps[0] + ":\n</p><p style='text-indent: 30px'>    " + ac_obj.get(_steps[0]) + "\n</p>"\
                  +"<p>" + _steps[1] + ":\n</p><p style='text-indent: 30px'>    " + ac_obj.get(_steps[1]) + "\n</p>"\
                  +"<p>" + _steps[2] + ":\n</p><p style='text-indent: 30px'>    " + ac_obj.get(_steps[2]) + "\n</p>"
    return content
 
def _init_testlink_client():
    key='c49d32b58989096d42282fd137ab58bc'
    url='https://testlink.successfactors.com/testlink/lib/api/xmlrpc/v1/xmlrpc.php'
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
