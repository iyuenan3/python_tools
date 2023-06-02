import argparse, requests, json, csv
from requests.auth import HTTPBasicAuth
from tabulate import tabulate
from datetime import datetime, timedelta

"""
我在 Nokia 工作时，我们会使用 Gerrit 来管理代码，每次提交一个 Commit，需要其他同事 Review 之后 +1、+2。
Commit +2 之后会触发 Zuul 调用 Jenkins Job 来跑 CI 测试，测试可能通过，也有可能失败。
CI 失败有可能是环境问题引起的，通常 regate 之后就能通过。也有可能是代码问题，那就需要提交一个 Patch 来修改代码，然后再找其他同事 Review。
如果需要提交新的 Patch，那有可能是该 Commit 的改动引入的，也有可能是代码冲突、环境配置变化等，这样的 Commit 需要被记录下来进一步分析，以提高代码质量。
这个脚本遍历了指定时间段内所有合入的代码，查询每个 commit 中 review+2 的次数，如果大于1次，就会记录到 csv 文件中，并在 console 上输出。
输出在 Console 上的示例如下：
+------------------------------------+-----------+--------------+----------------+
| change                             | owner     | regate_times | review+2_times |
+====================================+===========+==============+================+
| {Gerrit_API}/c/{Project}/+/8925234 | Zhang San |            1 |              3 |
+------------------------------------+-----------+--------------+----------------+
| {Gerrit_API}/c/{Project}/+/8887567 | Li Si     |            2 |              4 |
+------------------------------------+-----------+--------------+----------------+
| {Gerrit_API}/c/{Project}/+/8845819 | Wang Wu   |            0 |              2 |
+------------------------------------+-----------+--------------+----------------+
"""

Gerrit_USERNAME = "gerrit_username"
Gerrit_PASSWORD = "gerrit_password"
Gerrit_API      = "https://gerrit.com/gerrit"
Project         = "robottest"
RESULT_CSV      = 'problematic_changes.csv'

def get_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('--end', help='Specify the end date in the format "YYYY-MM-DD"')
    parser.add_argument('--start', help='Specify the start date in the format "YYYY-MM-DD"')
    args = parser.parse_args()
    if args.end:
        try:
            end_date = datetime.strptime(args.end, '%Y-%m-%d').date().strftime("%Y-%m-%d")
        except ValueError:
            print('Invalid date format!!! Please use the "YYYY-MM-DD".')
            exit(1)
    else:
        end_date = datetime.now().date().strftime("%Y-%m-%d")
    if args.start:
        try:
            start_date = datetime.strptime(args.start, '%Y-%m-%d').date().strftime("%Y-%m-%d")
        except ValueError:
            print('Invalid date format!!! Please use the "YYYY-MM-DD".')
            exit(1)
    else:
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(weeks=2)).strftime("%Y-%m-%d")
    return start_date, end_date

def get_info_from_api(url, params=None):
    response = requests.get(url, params=params, auth=HTTPBasicAuth(Gerrit_USERNAME, Gerrit_PASSWORD))
    if response.status_code == 200:
        content = response.text
        content = content.split('\n', 1)[1]
        info = json.loads(content)
        return info
    else:
        print(f'Failed to retrieve info. url: {url}, Status code: {response.status_code}')
        return []

def get_problematic_changes(total_changes):
    change_info_list = []
    for change in total_changes:
        messages_url  = f'{Gerrit_API}/a/changes/{change["id"]}/messages'
        owner_url     = f'{Gerrit_API}/a/accounts/{change["owner"]["_account_id"]}/'
        messages      = get_info_from_api(messages_url)
        owner         = get_info_from_api(owner_url)
        regate_times  = 0
        review2_times = 0
        for message in messages:
            if "regate" in message["message"]:
                regate_times += 1
            elif "Code-Review+2" in message["message"]:
                review2_times += 1
        if review2_times == 1:
            print(f'{change["_number"]} performed Code-Review+2 once, regate {regate_times} times, Pass')
            continue
        change_info = {
            "change": f'{Gerrit_API}/c/{Project}/+/{change["_number"]}',
            "subject": change["subject"],
            "owner": owner["name"],
            "regate_times": regate_times,
            "review+2_times": review2_times
        }
        print(f'{change["_number"]} performed Code-Review+2 {review2_times} times, regate {regate_times} times, Failed')
        change_info_list.append(change_info)
    return change_info_list

def save_result(total_changes, problematic_changes):
    total_changes_count       = len(total_changes)
    problematic_changes_count = len(problematic_changes)
    csvheader                 = ['change', 'subject', 'owner', 'regate_times', 'review+2_times']
    tableheader               = ['change', 'owner', 'regate_times', 'review+2_times']
    with open(RESULT_CSV, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csvheader)
        writer.writeheader()
        writer.writerows(problematic_changes)
    print(f'#### There are {total_changes_count} changes in the specified time period')
    print(f'#### There are {problematic_changes_count} changes Code-Review+2 more than 1 time')
    table  = [[item.get('change'), item.get('owner'), item.get('regate_times'), item.get('review+2_times')] for item in problematic_changes]
    print(tabulate(table, headers=tableheader, tablefmt='grid'))

if __name__ == '__main__':
    start_date, end_date      = get_argument()
    url                       = f'{Gerrit_API}/a/changes/'
    params                    = {'q': f'project:{Project} status:merged after:{start_date} before:{end_date}'}
    total_changes             = get_info_from_api(url, params)
    problematic_changes       = get_problematic_changes(total_changes)
    save_result(total_changes, problematic_changes)
