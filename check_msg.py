import json

with open('/home/zly/bsc/tsc/opencode-req.json') as f:
    data = json.load(f)

messages = data['messages']
for i, msg in enumerate(messages):
    role = msg['role']
    content = msg.get('content', '')
    if isinstance(content, list):
        for j, part in enumerate(content):
            if isinstance(part, dict) and 'text' in part:
                c = part['text'].count('The code almost writes itself after that')
                if c > 0:
                    preview = part['text'][:150].replace('\n', ' ')
                    print(f'msg[{i}] role={role} part[{j}]: count={c}')
                    print(f'  preview: {preview}...')
                    print()
    else:
        count = content.count('The code almost writes itself after that')
        if count > 0:
            preview = content[:150].replace('\n', ' ')
            print(f'msg[{i}] role={role} (str): count={count}')
            print(f'  preview: {preview}...')
            print()
