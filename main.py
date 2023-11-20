#!/usr/bin/env python
import json
import time
import sys
from WhisperTranscriber import WhisperTranscriber
from AwsUtils import Queue, Storage
import traceback
import datetime
import os

# This is the top level of a whisper-based audio transcription system.
# Audio URLs are removed from an SQS queue and streamed through whisper.
# The results are stored in S3.

def main():
    storage = Storage()
    instance_start_time = time.time()
    result = None
    base = {'SALAD_MACHINE_ID': os.environ.get('SALAD_MACHINE_ID', 'NA'),
            'SALAD_CONTAINER_GROUP_ID': os.environ.get('SALAD_CONTAINER_GROUP_ID', 'NA'),
            'instance_start': instance_start_time,
            'instance_start_datetime': datetime.datetime.utcfromtimestamp(instance_start_time).strftime('%Y-%m-%d %H:%M:%S'),
            }
    
    try:
        transcriber = WhisperTranscriber()
        queue = Queue()
        
        while True:
            base['elapsed_seconds_since_launch'] = time.time() - instance_start_time
            result = None
            msg = queue.get()
            if msg:
                base.update(msg)
                url, id = msg['url'], msg['id']
                result = transcriber.transcribe(url)
                result.update(base)
                storage.save(f'{id}.json', json.dumps(result) + '\n')
                print(f'processed {id}, result = {result}')
            else:
                print('waiting for input now')
    except Exception as e:
        error = {"exception": type(e).__name__, "traceback": traceback.format_exception(*sys.exc_info()) }
        error.update(base)
        if result:
            error.update(result)
        signature = instance_start_time
        storage.save(f'{signature}.failed', json.dumps(error) + '\n')
        print(error)
            
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        Queue().put({'id': 0, 'url': 'https://media.dharmaseed.org/recordings/sample.mp3'})
    main()
