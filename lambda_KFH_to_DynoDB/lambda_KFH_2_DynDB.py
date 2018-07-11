import json
import boto3
import logging
import base64

log = logging.getLogger()
log.setLevel(logging.INFO)

def lambda_data_handler(event, context):
    output = []
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table('Likes_Tab')
    log.info(event)
    for index, record in enumerate(event['records'],start=1):
        data = base64.b64decode(record['data'])
        log.info('Data is '+data)
        response = table.put_item(Item = json.loads(data))
        log.info(json.dumps(response))
        log.info("Row-" + str(index) + " written to DynamoDB successfully")
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(data)
        }
        output.append(output_record)
    log.info("Lambda processing finished. Now writing to S3 ...")
    return { 'records' : output }