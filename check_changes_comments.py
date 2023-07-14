import requests, json, sys
from requests.auth import HTTPBasicAuth

"""
最近有一个新需求，当 Gerrit 上某一个 Change 被 +2 之后，需要检查该 Change 是否有 Comments Unresolved。
通过 Gerrit API 可以通过 Change ID 获取到该 Change 的所有 Comments，每个 Comment 会有 id、author、
in_reply_to、updated、message、unresolved 等参数，第一个 Comment 没有 in_reply_to。每个 Comment 可能
会有多条回复。下面针对某一处改动的 Comment 进行处理。
获取该 Comment 下所有 Comment 的 id（unresolved==False 除外）和 in_reply_to，分别存入列表，comments_id
列表为 reply_id 列表的子列表，就可以证明该 Comment Resolved。
"""

Gerrit_USERNAME = "gerrit_username"
Gerrit_PASSWORD = "gerrit_password"
Gerrit_API      = "https://gerrit.com/gerrit"

def get_info_from_api(url, params=None):
    response = requests.get(url, params=params, auth=HTTPBasicAuth(Gerrit_USERNAME, Gerrit_PASSWORD))
    if response.status_code == 200:
        content = response.text
        content = content.split('\n', 1)[1]
        info = json.loads(content)
        return info
    else:
        print(f'Failed to retrieve info. url: {url}, Status code: {response.status_code}')
        sys.exit(1)

def check_comments_resolved(change_id):
    comments_url     = f'{Gerrit_API}/a/changes/{change_id}/comments'
    comments         = get_info_from_api(comments_url)
    unresolved_count = 0

    print(f'{change_id} COMMENTS INFO: {comments}')
    print("========================================")
    for comments_list in comments.values():
        comments_id = []
        reply_id    = []
        for comment in comments_list:
            if 'in_reply_to' in comment:
                reply_id.append(comment["in_reply_to"])
            if comment["unresolved"] == True:
                comments_id.append(comment["id"])
        if not set(comments_id).issubset(set(reply_id)):
            print(comments_list)
            print('ERROR: comment unresolved!!!')
            unresolved_count += 1
    return unresolved_count

def main():
    if len(sys.argv) != 2:
        print('ERROR INPUT')
        sys.exit(1)
    change_id = sys.argv[1]
    unresolved_count = check_comments_resolved(change_id)
    if unresolved_count > 0: sys.exit(1)

if __name__ == '__main__':
    main()
