import argparse, requests, json, csv
from requests.auth import HTTPBasicAuth
from tabulate import tabulate
from datetime import datetime, timedelta

Gerrit_USERNAME = "gerrit_username"
Gerrit_PASSWORD = "gerrit_password"
Gerrit_API      = "https://gerrit.com/gerrit"
Project         = "robottest"
RESULT_CSV      = 'merge_duration_statistics.csv'

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
    print(f'#### START DATE: {start_date}, END DATE: {end_date}')
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

def get_code_merge_duration(total_changes):
    change_info_list = []
    for change in total_changes:
        messages_url       = f'{Gerrit_API}/a/changes/{change["id"]}/messages'
        owner_url          = f'{Gerrit_API}/a/accounts/{change["owner"]["_account_id"]}/'
        messages           = get_info_from_api(messages_url)
        owner              = get_info_from_api(owner_url)
        merge_date         = None
        last_review2_date  = None
        first_review2_date = None

        for message in messages:
            if "Code-Review+2" in message["message"]:
                last_review2_date = message["date"].rstrip('0').ljust(26, '0')[:26]
                if first_review2_date is None:
                    first_review2_date = last_review2_date
            if "Starting post jobs" in message["message"]:
                merge_date = message["date"].rstrip('0').ljust(26, '0')[:26]

        merge_date         = datetime.strptime(merge_date, '%Y-%m-%d %H:%M:%S.%f')
        first_review2_date = datetime.strptime(first_review2_date, '%Y-%m-%d %H:%M:%S.%f')
        last_review2_date  = datetime.strptime(last_review2_date, '%Y-%m-%d %H:%M:%S.%f')
        review2_duration   = last_review2_date - first_review2_date
        merge_duration     = merge_date - last_review2_date

        hours, remainder           = divmod(review2_duration.total_seconds(), 3600)
        minutes, _                 = divmod(remainder, 60)
        review2_duration_formatted = f'{int(hours)}h {"%02d" % int(minutes)}m'
        hours, remainder           = divmod(merge_duration.total_seconds(), 3600)
        minutes, _                 = divmod(remainder, 60)
        merge_duration_formatted   = f'{int(hours)}h {"%02d" % int(minutes)}m'

        change_info = {
            "change": f'{Gerrit_API}/c/{Project}/+/{change["_number"]}',
            "subject": change["subject"],
            "owner": owner["name"],
            "review2_duration": review2_duration_formatted,
            "merge_duration": merge_duration_formatted
        }
        print(f'{change["_number"]} took {review2_duration_formatted} from first code_review+2 to last code_review+2')
        print(f'{change["_number"]} took {merge_duration_formatted} from last code_review+2 to code_merge')
        change_info_list.append(change_info)
    return change_info_list

def save_result(total_changes, code_merge_duration):
    total_changes_count       = len(total_changes)
    csvheader                 = ['change', 'subject', 'owner', 'review2_duration', 'merge_duration']
    tableheader               = ['change', 'owner', 'review2_duration', 'merge_duration']
    with open(RESULT_CSV, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csvheader)
        writer.writeheader()
        writer.writerows(code_merge_duration)
    print(f'#### There are {total_changes_count} changes in the specified time period')
    table  = [[item.get('change'), item.get('owner'), item.get('review2_duration'), item.get('merge_duration')] for item in code_merge_duration]
    print(tabulate(table, headers=tableheader, tablefmt='grid'))

if __name__ == '__main__':
    start_date, end_date      = get_argument()
    url                       = f'{Gerrit_API}/a/changes/'
    params                    = {'q': f'project:{Project} status:merged after:{start_date} before:{end_date}'}
    total_changes             = get_info_from_api(url, params)
    code_merge_duration       = get_code_merge_duration(total_changes)
    save_result(total_changes, code_merge_duration)
