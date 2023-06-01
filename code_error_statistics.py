
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

parser = argparse.ArgumentParser()
parser.add_argument('--date', help='Specify the date in the format "YYYY-MM-DD"')
parser.add_argument('--week', type=int, default=2, help='Specify the number of weeks')
args = parser.parse_args()
if args.date:
    try:
        END_DATE = datetime.strptime(args.date, '%Y-%m-%d').date().strftime("%Y-%m-%d")
    except ValueError:
        print('Invalid date format!!! Please use the "YYYY-MM-DD".')
        exit(1)
else:
    END_DATE = datetime.now().date().strftime("%Y-%m-%d")
START_DATE = (datetime.strptime(END_DATE, "%Y-%m-%d") - timedelta(weeks=args.week)).strftime("%Y-%m-%d")

Gerrit_USERNAME = "gerrit_username"
Gerrit_PASSWORD = "gerrit_password"
Gerrit_API      = "https://gerrit.com/gerrit"
Project         = "MN/5G/COMMON/aic-dep"

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

def get_problematic_changes():
    url              = f'{Gerrit_API}/a/changes/'
    params           = {'q': f'project:{Project} status:merged after:{START_DATE} before:{END_DATE}'}
    merged_changes   = get_info_from_api(url, params)
    change_info_list = []
    for change in merged_changes:
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

change_list = get_problematic_changes()
csv_name    = 'problematic_changes.csv'
header      = ['change', 'subject', 'owner', 'regate_times', 'review+2_times']
with open(csv_name, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=header)
    writer.writeheader()
    writer.writerows(change_list)
header = ['change', 'owner', 'regate_times', 'review+2_times']
table  = [[item.get('change'), item.get('owner'), item.get('regate_times'), item.get('review+2_times')] for item in change_list]
print(tabulate(table, headers=header, tablefmt='grid'))
