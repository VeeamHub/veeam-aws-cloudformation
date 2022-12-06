import cfnresponse
import json
import random
import string

def lambda_handler(event, context):
    print('Received event: %s' % json.dumps(event))
    
    status = cfnresponse.SUCCESS
    response = {}

    try:
        length = int(event['ResourceProperties']['Length'])

        if length < 2 or length > 1224:
            status = cfnresponse.FAILED
            return cfnresponse.send(event, context, status, response, reason='Length must be an integer between 2 and 1224')

    except KeyError:
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response, reason='Length must be specified')

    except:
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response, reason='Length must be an integer')

    if event['RequestType'] == 'Create':
        characters = string.ascii_letters + string.digits
        random_extid = ''.join(random.choices(characters, k=length))
        response = {'RandomExtId': random_extid}
        return cfnresponse.send(event, context, status, response)

    else:
        return cfnresponse.send(event, context, status, response)
