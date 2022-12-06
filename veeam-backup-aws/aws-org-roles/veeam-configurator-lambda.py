import cfnresponse
import json
import os
import urllib3

def lambda_handler(event, context):
    print('Received event: %s' % json.dumps(event))
    
    status = cfnresponse.SUCCESS
    response = {}
    
    # Pull values from the event
    accountId = event['ResourceProperties']['MemberAccountId']
    roleName = event['ResourceProperties']['RoleName']
    roleExtId = event['ResourceProperties']['RoleExtId']
    purpose = event['ResourceProperties']['Purpose']
    
    # Check for Delete event and send success to CloudFormation if so.
    # This function does not support changing or removing roles within Veeam Backup for AWS.
    if event['RequestType'] == 'Delete':
        info = 'IAM Role ' + roleName + ' from account ' + accountId + ' used for ' + purpose + ' operations has been deleted. Update your Veeam Backup for AWS configuration, if necessary. Sent success signal.'
        print(info)
        return cfnresponse.send(event, context, status, response)

    http = urllib3.PoolManager(cert_reqs='CERT_NONE')

    # Get credentials for the Veeam appliance from AWS Secrets Manager
    secrets_name = os.environ.get('SECRET_NAME')
    secrets_extension_endpoint = 'http://localhost:2773/secretsmanager/get?secretId=' + secrets_name
    secrets_headers = {'X-Aws-Parameters-Secrets-Token': os.environ.get('AWS_SESSION_TOKEN')}
    
    try:
        secrets_response = http.request('GET', secrets_extension_endpoint, headers = secrets_headers)
    except urllib3.exceptions.RequestError as err:
        print('There was an error making the request to AWS Secrets Manager: %s' % err)
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response)
    except urllib3.exceptions.ConnectionError as err:
        print('There was an error connecting to AWS Secrets Manager: %s' % err)
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response)

    if secrets_response.status != 200:
        print('Error retrieving the secret. Check permissions and the secret.')
        status = cfnresponse.FAILED
        cfnresponse.send(event, context, status, response)
    
    try:
        secret = json.loads(secrets_response.data.decode('utf-8'))['SecretString']
    except KeyError as err:
        print('No secret string found in the response from AWS Secrets Manager. Check your secret. Error: %s' % err)
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response)

    # Authenticate with the Veeam appliance
    veeam_ip = os.environ.get('VEEAM_INSTANCE_IP')
    veeam_api_endpoint = 'https://' + veeam_ip + ':11005/api/v1/'
    veeam_auth_endpoint = veeam_api_endpoint + 'token'
    veeam_auth_headers = {'x-api-version': '1.3-rev0','Content-Type': 'application/x-www-form-urlencoded','Accept': 'application/json'}
    
    try:
        veeam_username = json.loads(secret)['username']
    except KeyError as err:
        print('No username found in your secret. Check your secret. Error: %s' % err)
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response)
        
    try:
        veeam_password = json.loads(secret)['password']
    except KeyError as err:
        print('No password found in your secret. Check your secret. Error: %s' % err)
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response)
        
    veeam_auth_payload = {'grant_type': 'password', 'username': veeam_username, 'password': veeam_password}
    
    try:
        veeam_auth_response = http.request_encode_body('POST', veeam_auth_endpoint, fields = veeam_auth_payload, headers = veeam_auth_headers, encode_multipart=False)
    except urllib3.exceptions.RequestError as err:
        print('Error making the auth request to Veeam Backup for AWS. Error: %s' % err)
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response)
    except urllib3.exceptions.ConnectionError as err:
        print('Error connecting to Veeam Backup for AWS. Error: %s' % err)
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response)

    if veeam_auth_response.status != 200:
        print('Error authenticating with Veeam appliance. Check your secret and credentials on the appliance.')
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response)
    
    try:
        veeam_access_token = json.loads(veeam_auth_response.data.decode('utf-8'))['access_token']
    except KeyError as err:
        print('No access token was found in the response. Check your username and password for the appliance. Error: %s' % err)
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, response)
        
    veeam_token = 'Bearer ' + veeam_access_token

    # Add the account to the Veeam appliance
    if event['RequestType'] == 'Create':
        veeam_account_endpoint = veeam_api_endpoint + 'accounts/amazon'
        account_purpose = accountId + '-' + purpose
        veeam_account_payload = json.dumps({'name': account_purpose,'IAMRoleFromAnotherAccount': {'accountId': accountId,'roleName': roleName,'externalId': roleExtId}})
        veeam_account_headers = {'x-api-version': '1.3-rev0','Content-Type': 'application/json','Accept': 'application/json','Authorization': veeam_token}
        
        try:
            veeam_account_response = http.request('POST', veeam_account_endpoint, body = veeam_account_payload, headers = veeam_account_headers)
        except urllib3.exceptions.RequestError as err:
            print('Error making the account request to Veeam Backup for AWS. Error: %s' % err)
            status = cfnresponse.FAILED
            return cfnresponse.send(event, context, status, response)
        except urllib3.exceptions.ConnectionError as err:
            print('Error connecting to Veeam Backup for AWS. Error: %s' % err)
            status = cfnresponse.FAILED
            return cfnresponse.send(event, context, status, response)

        if veeam_account_response.status != 201:
            print('Error occurred and the account was not added. Check your configuration.')
            status = cfnresponse.FAILED
            return cfnresponse.send(event, context, status, response)
        
        return cfnresponse.send(event, context, status, response)

    else:
        info = 'Unsupported stack event. Sent success signal.'
        print(info)
        return cfnresponse.send(event, context, status, response)