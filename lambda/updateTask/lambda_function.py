import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Tasks')

def lambda_handler(event, context):
    try:
        task_id = event['pathParameters']['id']
        body = json.loads(event['body'])
        
        update_expressions = []
        expression_values = {}
        
        if 'taskName' in body:
            update_expressions.append('taskName = :taskName')
            expression_values[':taskName'] = body['taskName']
            
        if 'status' in body:
            update_expressions.append('#s = :status')
            expression_values[':status'] = body['status']
        
        response = table.update_item(
            Key={'id': task_id},
            UpdateExpression='SET ' + ', '.join(update_expressions),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames={'#s': 'status'} if 'status' in body else {},
            ReturnValues='ALL_NEW'
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Task updated successfully',
                'task': response['Attributes']
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