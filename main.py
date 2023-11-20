#!/usr/bin/env python
import json
import time
from WhisperTranscriber import WhisperTranscriber
from AwsUtils import Queue, Storage

# This is the top level of a whisper-based audio transcription system.
# Audio URLs are removed from an SQS queue and streamed through whisper.
# The results are stored in S3.

def main():
    start = time.time()
    transcriber = WhisperTranscriber()
    queue = Queue()
    storage = Storage()
    init_elapsed_seconds = time.time() - start
    
    while True:
        msg = queue.get()
        if msg:
            url, id = msg['url'], msg['id']
            result = transcriber.transcribe(url)
            result.update(msg)
            result['init_elapsed_seconds'] = init_elapsed_seconds
            storage.save(id, json.dumps(result) + '\n')
            print(f'processed {id}, result = {result}')
        else:
            print('waiting for input now')
            
if __name__ == '__main__':
    # Queue().put({'id': 0, 'url': 'https://media.dharmaseed.org/recordings/sample.mp3'})
    main()
