import sys, os, re, csv, requests
import xml.etree.ElementTree as ET
from tabulate import tabulate

"""
我在 Nokia 工作时，我们会利用 Jenkins Job 来跑一些 robot testcase。
在 TESTCASE_PATH 路径下会有很多 robot 文件，每份文件中包含一个或多个 testcase，每份文件头部会有一个 Force Tags 字段进行标记。
在 Jenkins Job Config 页面的 ./builders/hudson.tasks.Shell/command 中，通常会配置一些环境变量，比如 INCLUDE_TAG、EXCLUDE_TAG 等。
比如，INCLUDE_TAG=aaaANDbbb、EXCLUDE_TAG=cccORddd，那么该 Job 运行时会跑 Force Tags 中同时包含 aaa 和 bbb 并且不包含 ccc 和 ddd 的文件。
这个脚本可以获取每个 Job 的各个环境变量，并且记录每个 Job 运行了那些 robot 文件，用表格的形式输出在 Console 上并保存一份 csv 文件。
输出在 Console 上的示例如下：
+----------+-------------+---------------+-----------------+-------------+-----------------+
| JOB_NAME | ENV         | DEPLOYER_TOOL | INCLUDE_TAG     | EXCLUDE_TAG | NONCRITICAL_TAG |
+==========+=============+===============+=================+=============+=================+
| JOB_A    | Kubenetes_1 | tool_1        | aaaANDbbbANDccc | none        | 01              |
+----------+-------------+---------------+-----------------+-------------+-----------------+
| JOB_B    | Kubenetes_2 | tool_2        | aaaANDbbb       | 01          | 03OR04          |
+----------+-------------+---------------+-----------------+-------------+-----------------+
| JOB_C    | Kubenetes_3 | tool_3        | bbbANDccc       | 00OR02      | 03              |
+----------+-------------+---------------+-----------------+-------------+-----------------+
|:---------|:------|:------|:------|
| JOB_NAME | JOB_A | JOB_B | JOB_C |
| 00.robot | ●     | ●     |       |
| 01.robot | ○     |       | ●     |
| 02.robot | ●     | ●     |       |
| 03.robot | ●     | ○     | ○     |
| 04.robot | ●     | ○     | ●     |
"""

JOB_NAME_LIST = [
    'JOB_A',
    'JOB_B',
    'JOB_C'
]
TESTCASE_PATH    = "./robot/testcases"
JENKINS_URL      = 'http://192.168.111.222:1234'
JENKINS_USERNAME = 'jenkins_username'
JENKINS_PASSWORD = 'jenkins_password'
RESULT_CSV       = 'all_job_case_mapping.csv'

def get_all_job_config(all_testcase_tags):
    all_job_config = []
    for job_name in JOB_NAME_LIST:
        url = f'{JENKINS_URL}/job/{job_name}/config.xml'
        response = requests.get(url, auth=(JENKINS_USERNAME, JENKINS_PASSWORD))
        xml_content = response.text
        root = ET.fromstring(xml_content)
        command_element = root.find('./builders/hudson.tasks.Shell/command')
        if command_element is not None:
            command = command_element.text
            deployer_tool = re.search(r'DEPLOYER_TOOL=(\S+)', command).group(1)
            include_tag = re.search(r'INCLUDE_TAG=(\S+)', command).group(1)
            exclude_tag = re.search(r'EXCLUDE_TAG=(\S+)', command).group(1)
            noncritical_tag = re.search(r'NONCRITICAL_TAG=(\S+)', command).group(1)
            env = re.search(r'./run_test.sh (\S+)', command).group(1)
            critical_case = []
            exclude_case = []
            noncritical_case = []
            for item in all_testcase_tags:
                if set(include_tag.split('AND')).issubset(item['FORCE_TAG']) and not set(item['FORCE_TAG']).intersection(exclude_tag.split('OR')):
                    if set(item['FORCE_TAG']).intersection(noncritical_tag.split('OR')):
                        noncritical_case.append(item['CASE_NAME'])
                    else:
                        critical_case.append(item['CASE_NAME'])
                else:
                    exclude_case.append(item['CASE_NAME'])
            job_config_dict = {
                'JOB_NAME': job_name,
                'ENV': env,
                'DEPLOYER_TOOL': deployer_tool,
                'INCLUDE_TAG': include_tag,
                'EXCLUDE_TAG': exclude_tag,
                'NONCRITICAL_TAG': noncritical_tag,
                'CRITICAL_CASE': sorted(critical_case),
                'NONCRITICAL_CASE': sorted(noncritical_case),
                'EXCLUDE_CASE': sorted(exclude_case)
            }
            all_job_config.append(job_config_dict)
        else:
            print(f"Command element not found in the XML for job '{job_name}'.")
            sys.exit(1)

    headers = ['JOB_NAME', 'ENV', 'DEPLOYER_TOOL', 'INCLUDE_TAG', 'EXCLUDE_TAG', 'NONCRITICAL_TAG']
    table = [[item[key] for key in headers] for item in all_job_config]
    print(tabulate(table, headers, tablefmt='grid'))

    return all_job_config

def get_all_testcase_tags():
    all_testcase_tags = []
    for file_name in os.listdir(TESTCASE_PATH):
        file_path = os.path.join(TESTCASE_PATH, file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                for line in file:
                    if line.startswith("Force Tags"):
                        force_tags = line.strip().split()[2:]
                        testcase_tag = {
                            'CASE_NAME': file_name,
                            'FORCE_TAG': force_tags
                        }
                        all_testcase_tags.append(testcase_tag)
                        break
    return all_testcase_tags

def get_job_case_mapping(all_testcase_tags, all_job_config):
    case_names = set([tag['CASE_NAME'] for tag in all_testcase_tags])
    job_names = set([job['JOB_NAME'] for job in all_job_config])
    job_case_mapping = {}
    for job_name in job_names:
        job_case_mapping[job_name] = {}
        for case_name in case_names:
            job_case_mapping[job_name][case_name] = ''
    for job in all_job_config:
        job_name = job['JOB_NAME']
        for case_name in job['CRITICAL_CASE']:
            job_case_mapping[job_name][case_name] = '●'
        for case_name in job['NONCRITICAL_CASE']:
            job_case_mapping[job_name][case_name] = '○'
        for case_name in job['EXCLUDE_CASE']:
            job_case_mapping[job_name][case_name] = ''

    with open(RESULT_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([''] + sorted(job_names))
        for case_name in sorted(case_names):
            row = [case_name]
            for job_name in sorted(job_names):
                row.append(job_case_mapping[job_name][case_name])
            writer.writerow(row)

    with open(RESULT_CSV, 'r') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
        table = tabulate(data, tablefmt='pipe')
        print(table)

if __name__ == '__main__':
    all_testcase_tags = get_all_testcase_tags()
    all_job_config = get_all_job_config(all_testcase_tags)
    get_job_case_mapping(all_testcase_tags, all_job_config)
