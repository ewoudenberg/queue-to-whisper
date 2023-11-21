#!/usr/bin/env python
import datetime
import json
import os
import sys
import time
import traceback

from AwsUtils import Queue, Storage
from WhisperTranscriber import WhisperTranscriber
from SaladAPI import Salad

# This is the top level of a whisper-based audio transcription system.
# Audio URLs are removed from an SQS queue and streamed through whisper.
# The results are stored in S3.

MAX_IDLE_SECONDS_BEFORE_SHUTDOWN = (2*60) # AWS SQS Documentation says that a queue's "approximate" attributes settle within one minute.

def main():
    storage = Storage()
    instance_start_time = time.time()
    result = None
    base = {'SALAD_MACHINE_ID': os.environ.get('SALAD_MACHINE_ID', 'NA'),
            'SALAD_CONTAINER_GROUP_ID': os.environ.get('SALAD_CONTAINER_GROUP_ID', 'NA'),
            'instance_start': instance_start_time,
            'instance_start_datetime': datetime.datetime.utcfromtimestamp(instance_start_time).strftime('%Y-%m-%d %H:%M:%S'),
            }
    
    queue = None
    try:
        transcriber = WhisperTranscriber()
        queue = Queue()
        base['seconds_to_initialize'] = time.time() - instance_start_time
        idling_started = None
        
        while True:
            result = None
            msg = None
            msg = queue.get()
            if msg:
                idling_started = None
                base.update(msg)
                url, id = msg['url'], msg['id']
                result = transcriber.transcribe(url)
                result.update(base)
                storage.save(f'{id}.json', json.dumps(result, indent=2) + '\n')
                print(f'processed {id}')

            else:
                if idling_started:
                    idle_time = time.time() - idling_started
                    if idle_time > MAX_IDLE_SECONDS_BEFORE_SHUTDOWN and queue.is_empty():
                        print('Shutting down Salad Container Group')
                        Salad().shutdown()
                        break
                else:
                    idling_started = time.time()
                    print('Idling')

    except Exception as e:
        if msg and queue:
            queue.delete()
            queue.put(msg)
        error = {"exception": type(e).__name__, "traceback": traceback.format_exception(*sys.exc_info()) }
        error.update(base)
        if result:
            error.update(result)
        signature = instance_start_time
        storage.save(f'{signature}.failed', json.dumps(error, indent=2) + '\n')
        print(error)
        Salad().reallocate()
        
            
if __name__ == '__main__':
    #if len(sys.argv) > 1 and sys.argv[1] == 'test':
    Queue().put({'id': 0, 'url': 'https://media.dharmaseed.org/recordings/sample.mp3'})
    main()
