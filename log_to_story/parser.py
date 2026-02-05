from collections import defaultdict
import re
from dateutil import parser as dparser
from datetime import datetime

SSH_FAILED_RE = re.compile(r"(?P<prefix>.*?)?(?P<ts>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*?(Failed password|Authentication failure|authentication failure) for(?: invalid user)? (?P<user>\S+) from (?P<ip>\d+\.\d+\.\d+\.\d+)")
SSH_ACCEPTED_RE = re.compile(r"(?P<prefix>.*?)?(?P<ts>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*?(Accepted password|session opened for user|Accepted publickey) for (?P<user>\S+) from (?P<ip>\d+\.\d+\.\d+\.\d+)")

def _parse_syslog_ts(ts_str):
    # syslog has no year; assume current year
    try:
        year = datetime.now().year
        dt = dparser.parse(f"{ts_str} {year}")
        return dt
    except Exception:
        return None

def parse_log(text):
    """Parse auth/syslog-like text and return summarized events.

    Returns dict with:
    - events: list of parsed events
    - summary: aggregated counts by user/ip
    """
    events = []
    summary = {
        'failed_by_user': defaultdict(int),
        'failed_by_ip': defaultdict(int),
        'success_by_user': defaultdict(int),
        'success_by_ip': defaultdict(int),
    }

    for line in text.splitlines():
        m = SSH_FAILED_RE.search(line)
        if m:
            ts = _parse_syslog_ts(m.group('ts'))
            user = m.group('user')
            ip = m.group('ip')
            events.append({'type':'failed', 'ts':ts, 'user':user, 'ip':ip, 'raw':line})
            summary['failed_by_user'][user] += 1
            summary['failed_by_ip'][ip] += 1
            continue

        m2 = SSH_ACCEPTED_RE.search(line)
        if m2:
            ts = _parse_syslog_ts(m2.group('ts'))
            user = m2.group('user')
            ip = m2.group('ip')
            events.append({'type':'success', 'ts':ts, 'user':user, 'ip':ip, 'raw':line})
            summary['success_by_user'][user] += 1
            summary['success_by_ip'][ip] += 1
            continue

    return {'events': events, 'summary': summary}


def analyze_findings(parse_result, failed_threshold=5, window_minutes=5):
    """Analyze parsed events for patterns (brute force, post-failure success).

    Adds a `findings` list to the parse_result and returns it.
    """
    from datetime import timedelta

    events = [e for e in parse_result['events'] if e.get('ts')]
    events.sort(key=lambda x: x['ts'])
    findings = []

    # Detect many failed attempts from same IP or for same user within sliding window
    by_ip = defaultdict(list)
    by_user = defaultdict(list)
    for e in events:
        if e['type'] == 'failed':
            by_ip[e['ip']].append(e)
            by_user[e['user']].append(e)

    def detect_burst(bucket, key_name):
        for key, evs in bucket.items():
            start = 0
            for i in range(len(evs)):
                # advance start while window too large
                while evs[i]['ts'] - evs[start]['ts'] > timedelta(minutes=window_minutes):
                    start += 1
                count = i - start + 1
                if count >= failed_threshold:
                    findings.append({
                        'type': 'brute_force',
                        'target': key,
                        'target_type': key_name,
                        'count': count,
                        'start_ts': evs[start]['ts'],
                        'end_ts': evs[i]['ts'],
                        'description': f"{count} failed logins for {key_name} {key} between {evs[start]['ts']} and {evs[i]['ts']}"
                    })
                    break

    detect_burst(by_ip, 'ip')
    detect_burst(by_user, 'user')

    # Detect success following failures from same IP within window
    successes = [e for e in events if e['type'] == 'success']
    for s in successes:
        ip = s['ip']
        recent_fails = [f for f in by_ip.get(ip, []) if 0 <= (s['ts'] - f['ts']).total_seconds() <= window_minutes * 60]
        if recent_fails:
            findings.append({
                'type': 'post_failure_success',
                'ip': ip,
                'user': s['user'],
                'success_ts': s['ts'],
                'fail_count': len(recent_fails),
                'description': f"Successful login for {s['user']} from {ip} at {s['ts']} after {len(recent_fails)} recent failures"
            })

    parse_result['findings'] = findings
    return findings

