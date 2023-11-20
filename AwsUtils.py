import json
import boto3
from aws_secrets import *


class Queue:
    def __init__(self):
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION)
        self.sqs = session.client('sqs')
        self.last_receipt_handle = None

    def get(self):
        """Remove the previous item from the queue and return the next one, if present"""
        if self.last_receipt_handle:
            self.sqs.delete_message(QueueUrl = SQS_URL, ReceiptHandle = self.last_receipt_handle)
            self.last_receipt_handle = None
        
        response = self.sqs.receive_message(QueueUrl = SQS_URL, WaitTimeSeconds=1)
        if 'Messages' in response and response['Messages']:
            message = response['Messages'][0]
            self.last_receipt_handle = message['ReceiptHandle']
            return json.loads(message['Body'])
        
        return None
    
    def put(self, python_dict):
        """Put the python dictionary on the queue as a JSON string"""
        json_str = json.dumps(python_dict)
        self.sqs.send_message(QueueUrl = SQS_URL, MessageBody=json_str)
        

class Storage:
    def __init__(self):
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION)
        self.s3 = session.client('s3')

    def save(self, key, body):
        """Store the transcription result in our S3 bucket with the name {id}.json"""
        key = f'large-v3/english/{key}'
        self.s3.put_object(Bucket=BUCKET, Key=key, Body=body)

if __name__ == '__main__':
    q = Queue()
    print('q.get', q.get())
    s = Storage()
