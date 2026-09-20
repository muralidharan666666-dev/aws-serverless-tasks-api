
import boto3
import json
import hmac
import hashlib
import base64

def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(
        client_secret.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def lambda_handler(event, context):
    client = boto3.client('cognito-idp',
                         region_name='us-east-1')

    username = 'YOUR-EMAIL-HERE'
    client_id = 'YOUR-CLIENT-ID-HERE'
    client_secret = 'YOUR-CLIENT-SECRET-HERE'

    secret_hash = get_secret_hash(
        username,
        client_id,
        client_secret
    )

    try:
        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': 'YOUR-PASSWORD-HERE',
                'SECRET_HASH': secret_hash
            }
        )

        token = response['AuthenticationResult']['IdToken']

        return {
            'statusCode': 200,
            'body': json.dumps({
                'token': token
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }   