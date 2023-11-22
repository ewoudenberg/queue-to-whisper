#!/usr/bin/env python3

# Pretty-Print the transcription output json file.

import json
import sys
from addict import Dict

def main():
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} [--raw-text <transcription-output.json> [...] ; Pretty-print the json output of the Whisper transcription process.')
        sys.exit(1)
        
    raw_text = False
    argv = sys.argv[1:]
    if argv[0] == '--raw-text':
        argv = sys.argv[2:]
        raw_text = True

    total_elapsed = total_duration = 0
            
    for fn in argv:
        with open(fn) as f:
            transcription = Dict(json.load(f))
            
        if not transcription.duration_in_minutes:
            continue
        
        if not raw_text:
            print(f'{transcription.teacher}: {transcription.title}')
            factor = transcription.duration_in_minutes * 60 / transcription.elapsed_seconds
            total_elapsed += transcription.elapsed_seconds
            total_duration += transcription.duration_in_minutes * 60
            elapsed_seconds_since_launch = transcription.init_elapsed_seconds or transcription.elapsed_seconds_since_launch or transcription.seconds_to_initialize
            print(f'{transcription.SALAD_MACHINE_ID} Transcribed in {int(transcription.elapsed_seconds):4d} seconds, realtime factor: {factor:6.2f}x, seconds to initialize = {elapsed_seconds_since_launch:6.2f} {transcription.url[48:100]}\n')
        for chunk in transcription.chunks:
            if raw_text:
                print(chunk.text)
            else:
                print(f'{format_timestamp(chunk.timestamp)}', chunk.text)
            
    if not raw_text:
        print(f'Overall realtime factor = {total_duration}/{total_elapsed} = {total_duration/total_elapsed}')
    
def format_timestamp(start_end):
    start, end = start_end
    return f'{format_duration(start)} - {format_duration(end)}'
    
def format_duration(seconds):
    # Calculate the hours, minutes, and remaining seconds
    if seconds == None:
        return '         '
    hours = seconds // 3600
    remaining_seconds = seconds % 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60

    result = ''
    # Format the output as "HHhMMmSSs"
    for part in (hours, 'h'), (minutes, 'm'), (seconds, 's'):
        result += f'{int(part[0]):02}{part[1]}' if part[0] or result.strip() else '   '
    return result

if __name__ == '__main__':
     main()