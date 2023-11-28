#!/usr/bin/env python
import datetime
import os
import sys
import threading
import time
import traceback

from AwsUtils import Queue, Storage
from WhisperTranscriber import WhisperTranscriber
from SaladAPI import Salad

# This is the top level of a whisper-based audio transcription system.
# Audio URLs are removed from an SQS queue and streamed through whisper.
# The results are stored in S3.

MAX_IDLE_SECONDS_BEFORE_SHUTDOWN = (2*60) # AWS SQS Documentation says that a queue's "approximate" attributes settle within one minute.
MIN_REALTIME_FACTOR = 22 # Abandon any nodes that are not running at at least this realtime factor

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
    timer = None
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
                base.update(msg)
                idling_started = False
                url, id = msg['url'], msg['id']
                timer = start_performance_timer(msg, base)
                result = transcriber.transcribe(url)
                timer.cancel()
                result.update(base)
                result['instance_exit_time'] = time.time()
                storage.save(f'{id}.json', result)
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
        if timer:
            timer.cancel()
        if msg and queue:
            queue.delete()
            queue.put(msg)
        error = {"exception": type(e).__name__, "traceback": traceback.format_exception(*sys.exc_info()) }
        error.update(base)
        if result:
            error.update(result)
        signature = instance_start_time
        error['instance_exit_time'] = time.time()
        storage.save(f'{signature}.failed', error)
        print(error)
        Salad().reallocate()
    
def node_too_slow(msg, base):
    """Called when the "node-too-slow" timer expires while transcribing. 
       We put the msg back on the queue and arrange that this node is not used again."""
    queue = Queue()
    queue.delete()
    queue.put(msg)    
    Storage().save(f'{msg["id"]}.slow', base)
    Salad().reallocate()
    
def start_performance_timer(msg, base):
    """Start a timer based on the duration of the recording and the real-time processing factor we require.
       Add in 1 minute to cover any startup latencies.
    """
    minutes = float(msg.get('duration_in_minutes', 0)) + 1
    timeout =  minutes * 60 / MIN_REALTIME_FACTOR
    timer = threading.Timer(interval = timeout, function = node_too_slow, args = [msg, base])
    timer.start()
    return timer
    
            
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        Queue().put({'id': 0, 'url': 'https://media.dharmaseed.org/recordings/sample.mp3'})
    main()
