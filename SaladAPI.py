import os
import requests
import json
from aws_secrets import *

HEADERS = {
    "accept": "application/json",
    "Salad-Api-Key": SALAD_API_KEY
}

class Salad:
    def __init__(self):
        self.machine_id = os.environ.get('SALAD_MACHINE_ID')
        self.container_id = os.environ.get('SALAD_CONTAINER_GROUP_ID')
        self.container_name = self.getContainerName()
        
    def getContainerName(self):
        url = "https://api.salad.com/api/public/organizations/dharmaseed/projects/talk-transcription/containers"
        payload = requests.get(url, headers=HEADERS)
        response = json.loads(payload.text)
        for container in response['items']:
            if container['id'] == self.container_id:
                return container['name']

    def shutdown(self):
        url = f"https://api.salad.com/api/public/organizations/dharmaseed/projects/talk-transcription/containers/{self.container_name}/stop"
        requests.post(url, headers=HEADERS)
        
    def reallocate(self):
        url = f"https://api.salad.com/api/public/organizations/dharmaseed/projects/talk-transcription/containers/{self.container_name}/instances/{self.machine_id}/reallocate"
        requests.post(url, headers=HEADERS)

