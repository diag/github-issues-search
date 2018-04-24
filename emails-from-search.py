import json
import pprint
import csv
import os
import requests

def get_email_from_events(url, access_token):
    api_url = "{0}?access_token={1}".format(url, access_token)
    print('querying: %s' % api_url)
    r = requests.get(api_url)
    events = r.json()

    # Get first email mentioned in a commit, heuristic but should be most likely to be the person we are targeting
    for e in events:
        if 'payload' in e:
            if 'commits' in e['payload'] and isinstance(e['payload']['commits'], list) and len(e['payload']['commits']) > 0:
                if 'author' in e['payload']['commits'][0]:
                    return e['payload']['commits'][0]['author']
    return None

def get_user_events_url(user):
    if user is None or 'login' not in user:
        return ''
    return 'https://api.github.com/users/%s/events/public' % user['login']

def append_if_valid(row, str, arr):
    if len(str) > 0:
        arr.append({ 'url': str, 'repo': row['repo'], 'repo_html_url': row['repo_html_url'] })

if __name__ == '__main__':
    access_token = os.environ['GITHUB_ACCESS_TOKEN']
    f = open('logs.json', 'r')
    j = json.load(f)
    urls = []
    deduped = []
    for row in j:
        if 'comments' in row:
            for comment in row['comments']:
                append_if_valid(row, get_user_events_url(comment['user']), urls)
        append_if_valid(row, get_user_events_url(row['user']), urls)
        append_if_valid(row, get_user_events_url(row['assignee']), urls)

    tmp = []
    for url in urls:
        if url['url'] not in tmp:
            tmp.append(url['url'])
            deduped.append(url)

    results = []
    count = 0
    for url in deduped:
        count += 1
        author = get_email_from_events(url['url'], access_token)
        if author is not None:
            row = url.copy()
            row.update(author)
            results.append(row)
        # if count > 5:
        #     break

    f = open('emails.json', 'w')
    json.dump(results, f)

    with open('emails.csv', 'w') as csvfile:
        fieldnames = ['repo', 'repo_html_url', 'name', 'email', 'url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in results:
            writer.writerow({k: v.encode('utf8') for k, v in row.items()})



    
