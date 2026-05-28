import boto3
import json
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Tasks')

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        
        task_id = str(uuid.uuid4())
        task_name = body['taskName']
        
        table.put_item(Item={
            'id': task_id,
            'taskName': task_name,
            'status': 'pending'
        })
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Task created successfully',
                'taskId': task_id
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }