#!/usr/bin/env python3
import re
import os

def sanitize_cc_request(content):
    replacements = [
        (r'sk-ant-oat01-[A-Za-z0-9-]+', '[REDACTED_ANTHROPIC_API_KEY]'),
        (r'X-Claude-Code-Session-Id: [a-f0-9-]+', 'X-Claude-Code-Session-Id: [REDACTED_SESSION_ID]'),
        (r'x-client-request-id: [a-f0-9-]+', 'x-client-request-id: [REDACTED_REQUEST_ID]'),
        (r'anthropic-organization-id: [a-f0-9-]+', 'anthropic-organization-id: [REDACTED_ORG_ID]'),
        (r'request-id: req_[A-Za-z0-9]+', 'request-id: [REDACTED_REQ_ID]'),
        (r'traceresponse: [0-9a-f-]+', 'traceresponse: [REDACTED_TRACE_ID]'),
        (r'set-cookie: [^\n]+', 'set-cookie: [REDACTED_COOKIE]'),
        (r'cf-ray: [a-f0-9]+-[A-Z]+', 'cf-ray: [REDACTED_CF_RAY]'),
        (r'/home/rbtest0034/test/cc_test/', '/home/user/project/'),
        (r'/home/rbtest0034/test/', '/home/user/project/'),
        (r'/home/rbtest0034/ai_agent/', '/home/user/data/'),
    ]
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    return content

def sanitize_opencode_request(content):
    replacements = [
        (r'x-opencode-request: msg_[A-Za-z0-9]+', 'x-opencode-request: [REDACTED_REQUEST_ID]'),
        (r'x-opencode-session: ses_[A-Za-z0-9]+', 'x-opencode-session: [REDACTED_SESSION_ID]'),
        (r'"id":"[0-9a-f-]{8}-[0-9a-f-]{4}-[0-9a-f-]{4}-[0-9a-f-]{4}-[0-9a-f-]{12}"', '"id":"[REDACTED_CHUNK_ID]"'),
        (r'CF-RAY: [a-f0-9]+-[A-Z]+', 'CF-RAY: [REDACTED_CF_RAY]'),
        (r'/home/rbtest0034/test/bsc_str_lib-master/', '/home/user/project/'),
        (r'/home/rbtest0034/test/', '/home/user/project/'),
        (r'/home/rbtest0034/ai_agent/', '/home/user/data/'),
    ]
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    return content

def main():
    base_dir = '/home/rbtest0034/ai_agent'
    
    cc_file = os.path.join(base_dir, 'cc.req')
    cc_sanitized = os.path.join(base_dir, 'cc.req.sanitized')
    with open(cc_file, 'r', errors='replace') as f:
        content = f.read()
    content = sanitize_cc_request(content)
    with open(cc_sanitized, 'w') as f:
        f.write(content)
    print(f"Sanitized: {cc_sanitized}")
    
    opencode_file = os.path.join(base_dir, 'opencode.req')
    opencode_sanitized = os.path.join(base_dir, 'opencode.req.sanitized')
    with open(opencode_file, 'r', errors='replace') as f:
        content = f.read()
    content = sanitize_opencode_request(content)
    with open(opencode_sanitized, 'w') as f:
        f.write(content)
    print(f"Sanitized: {opencode_sanitized}")

if __name__ == '__main__':
    main()
