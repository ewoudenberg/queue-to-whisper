#!/usr/bin/env python3
from AwsUtils import Queue

try:
    with open('nextid') as f:
        id = int(f.read())
except:
    id = 10
with open('nextid', 'w') as f:
    f.write(str(id+1))
print('Using id', id)
Queue().put({"id": id, "url": "https://media.dharmaseed.org/recordings/sample.mp3"})
