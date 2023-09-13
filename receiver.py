#!/bin/env python

from simplejson.errors import JSONDecodeError
import time
import requests

KEYWORD="testalternatecommunications"
page_size=40
public_timeline_path=f"/api/v1/timelines/public?limit={page_size}"

public_tags_path=f"/api/v1/timelines/tag/"

hosts = []
failed_hosts = [] 


def log_error(msg: str):
    print(f"[ERROR] {msg}")


def fetch_public_timeline(host: str):
    resp = requests.get(f"https://{host}/{public_timeline_path}")
    if resp.status_code != 200:
        log_error(f"Failed federated posts at: {host} {resp.status_code}")
        failed_hosts.append(failed_hosts)
        return None
    
    try:
        return resp.json()
    except JSONDecodeError as e:
        log_error(f"Failed to parse json with 200 response on host {host}")

def extract_hosts_from_timeline(seed: str):
    timeline = fetch_public_timeline(seed)
    if timeline == None:
        return None

    host = []
    if type(timeline) == str:
            print(f"Timeline was string: {timeline}")
            return None
    for message in timeline:
        index=1
        parts = message['account']['acct'].split('@')
        if 'url' in message['account'] and len(parts) < 2:
            parts = message['account']['url'].split('/')
            index=2
        
        if len(parts) < 2:
            log_error(f"Couldn't get domain from account {message['account']['acct']} in {message['account']}")
            continue

        h = parts[index]

        if h.strip() == "" or h is None:
            log_error(f"Extracted host was empty {message['account']}")
            return None


        host.append(h) if h not in host else None
    return host

def seed_hosts(seed_host: str):
    hosts.extend(extract_hosts_from_timeline(seed_host))

    visited = [seed_host]

    for host in hosts.copy():
        print(f"Seeding {host}")
        if host in visited or host in failed_hosts:
            continue

        visited.append(host)

        found_hosts = extract_hosts_from_timeline(host)
        if found_hosts == None:
            continue
        for h in found_hosts:
            hosts.append(h) if h not in hosts else None


def message_processor(host: str) -> bool:
    print(f"Trying host: {host}")
    global KEYWORD
    global hosts
    resp = requests.get(f"https://{host}/{public_tags_path}/{KEYWORD}")
    if resp.status_code != 200:
        log_error(f"Failed to pull tag search {resp.status_code}: {resp.content} ")
        failed_hosts.append(hosts.pop(hosts.index(host)))
        return False
    j = None
    
    try:
        j = resp.json()
    except JSONDecodeError as exc:
        log_error(f"Failed to parse json from API[{resp.status_code}]: {resp.content}")
        failed_hosts.append(hosts.pop(hosts.index(host)))
        return False
    
    print(f"Found {len(j)} messages to handle")
    if len(j) > 0:
        last_msg = j[-1]
        print(f"Most recent message was: {last_msg['content']}")
    print("Sleeping...")
    time.sleep(10)
    return True

print(f"\n\nLooking for keyword tag: {KEYWORD}")

while True:
    seed_hosts("botsin.space")

    print(f"Seeded {len(hosts)} domains")
    print(hosts)

    if True not in [message_processor(host) for host in hosts]:
        log_error("No attempt at seaching for tags succeeded, bailing...")
        exit(1)