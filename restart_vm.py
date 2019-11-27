import os
import pprint

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-cloud-credentials.json'
credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials)

# Project ID for this request.
project = 'rock-idiom-260222'
# The name of the zone for this request.
zone = 'us-east4-c'
# Name of the instance resource to start.
instance = 'census-api'

# Reset the instance
request = service.instances().reset(project=project, zone=zone, instance=instance)
response = request.execute()
pprint.pprint(response)