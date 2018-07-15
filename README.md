# A basic AWS Pipeline to stream JSON from Firehose to DynamoDB using Lambda

This project is meant to demonstrate beginner AWS users a basic AWS pipeline for a single JSON event generated by AWS CLI streamed through Kinesis Firehose delivery stream and using AWS Lambda for transformation before being written to DynamoDB. A pre-created S3 bucket is chosen as the destination of the Firehose delivery stream. This document gives a step-by-step guide for the configuration / set-up of the required AWS services as well as both custom and managed AWS policies needed as well as the details of the Python lambda data handler doing the transformation together with some screenshots.

# Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing purpose. 

# Pre-requisites
There are certain pre-requisites to make this project work from local or whatever deployment environment you are using.
1.	Need an AWS account
2.	Need to download and install AWS CLI MSI Installer for Windows from here. By default, the AWS CLI will be installed under C:\Program Files\Amazon\AWSCLI 
3.	Need to have Python installed in the deployment environment (minimum version >= 2.7). In this example, Python 2.7.13 is used
# Configuration / Set-up of AWS Services

1.	Create a DynamoDB table where AWS Lambda should write the sample data into. You can give any AWS supported table name but the structure of the table should be like as below. 
Since the showcased input JSON event is 
```
"data": "{\"element_class\":\"1001\"}"
```

we create a table `Likes_Tab`, chose Partition key as `element_class` (Type: String), no Sort Key and probably with no indexes since that incurs price. See Pricing on indexes.

![Alt text](/images/db_ss.jpg?raw=true "DynamoDB snapshot")

You must stream-enable the DynamoDB table and below is the screenshot of the overview 

![Alt text](/images/tab_ovw.jpg?raw=true "DynamoDB table overview")


2.	Create an S3 bucket meant to be destination for the firehose delivery stream.

Give an AWS-supported bucket name and specify the region. 
Don’t set any properties like Versioning, Server access logging, Tags, Object-level logging, Default encryption and keep them as default.
Neither grant any public read access permission nor any S3 Delivery group write access on this bucket. 
Grant no read, write permissions to any AWS Accounts but the bucket owner.

![Alt text](/images/S3_bucket.jpg?raw=true "S3 bucket")


3.	Download ZIP or clone the repository in a local directory. Extract the ZIP and add the folder ‘lambda_KFH_2_DynDB.py’ with its all contents to a separate deployment ZIP package (e.g. ‘lambda_KFH_2_DynDB.zip’) to be uploaded into AWS Lambda function

To find how to manually create the deployment ZIP package, please check here. 

4.	In the AWS Lambda screen, create a Lambda function (e.g. `lambda_KFH_to_DynoDB`) and upload the deployment package ZIP (e.g. ‘lambda_KFH_2_DynDB.zip’).

![Alt text](/images/lambda_1.jpg?raw=true "Lambda upload zip")



You can test the functionality of the uploaded deployment package by creating and configuring a test event as follows. In your case, you must give the Kinesis firehose delivery stream name that you have created in your AWS account, specify the region of the Firehose delivery stream and most importantly, provide the sample JSON event under the `data` attribute. In below screenshot, input sample JSON event as
```
"data": "{\"element_class\":\"1001\"}"
```

![Alt text](/images/test_evnt.jpg?raw=true "Configure test event")


Note: Please remember to change the table name in the Python AWS Lambda function to the DynamoDB table that you have created. Because by default, the lambda function writes to a DynamoDB table named `Likes_Tab` as per shown example.


5.	Create a Firehose delivery stream with source specified as `Direct PUT and other sources` and destination as the S3 bucket created in Step 2. You can optionally specify a prefix for S3 destination like we have chosen `kinesis_firehose_input`. Also, specify the lambda function you created (e.g. `lambda_KFH_to_DynoDB`) in Step 4 as Record transformation for the delivery stream.

![Alt text](/images/firehose_dlv_strm_1.jpg?raw=true "Firehose delivery stream - record transformation") 

We used runtime Python2.7 for execution of the AWS Lambda function. 
Buffer conditions is either 3MB or 60 seconds whichever is earlier for writing to S3.
Timeout is 1 minute 3 seconds.
Record format conversion or Source S3 backup are disabled as they also incur pricing.
CloudWatch error logging is enabled by default.
The IAM role created for the Firehose delivery stream is `kinesisfullaccess`. More on roles / permissions, see IAM Roles and Policies section.

![Alt text](/images/firehose_dlv_strm_2.jpg?raw=true "Firehose delivery stream - details")
 
6.	For generating Firehose events, AWS CLI Put-Record utility is used. 

Need to configure the AWS CLI to authenticate using the AWS Account you want to use. Specify respectively Access Key ID, Secret Access Key, region name as well as the output format. 

![Alt text](/images/aws_access.jpg?raw=true "AWS CLI Access") 

From the directory where AWS CLI is installed, run the command 
```
c:\Program Files\Amazon\AWSCLI>aws firehose put-record --delivery-stream-name <your_firehose_delivery_stream_name> --record file://C:/Users/.../likes_data_single.json
```
Below is the screenshot of the RecordId returned by firehose with the binary encoded response after successful posting of event into the delivery stream.

![Alt text](/images/aws_put_rec.jpg?raw=true "AWS CLI Put-Record") 

The data file `likes_data_single.json` contains a single line with the below content:
```
{"Data":"{\"element_class\":\"1001\"}\n"}
```
Important: The data file contains a String representation of a JSON event (i.e. "{\"element_class\":\"1001\"}\n") entered as a String value for ‘Data’ attribute.

Note: You can also enter a batch of records by adding multiple lines to the JSON file.

# IAM Roles and Policies

We need to create three different roles for the AWS pipeline to function without any access permission problems.

## Kinesis Firehose Role to transform and deliver data to DynamoDB through Lambda

For the beginning user who has little experience with IAM roles and policies, the Kinesis Firehose role can comprise four permissions policies to work with – 

* AWSLambdaFullAccess – AWS managed policy
* AmazonKinesisFullAccess – AWS managed policy
* AmazonKinesisFirehoseFullAccess – AWS managed policy
* oneClick_firehose_delivery_role_XXXXXXXXXXXXX – Inline policy

![Alt text](/images/kinesis_role_summ.jpg?raw=true "Kinesis Role Summary") 

The inline policy `oneClick_firehose_delivery_role_XXXXXXXXXXXXX` is an IAM role created to read schema from Glue table, read/write/list from S3 bucket, invoke/access the lambda function, writing firehose logs to delivery stream log group via CloudWatch, access to kinesis/firehose streams and kms encrypt/decrypt. 
It comprises the following access permissions –
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "glue:GetTableVersions"
            ],
            "Resource": "*"
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:GetBucketLocation",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:ListBucketMultipartUploads",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::<your_S3_bucket_name>",
                "arn:aws:s3::: <your_S3_bucket_name>/*",
                "arn:aws:s3:::%FIREHOSE_BUCKET_NAME%",
                "arn:aws:s3:::%FIREHOSE_BUCKET_NAME%/*"
            ]
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction",
                "lambda:GetFunctionConfiguration"
            ],
            "Resource": "arn:aws:lambda:xx-xxxx-x:XXXXXXXXXXXX:function:%FIREHOSE_DEFAULT_FUNCTION%:%FIREHOSE_DEFAULT_VERSION%"
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:xx-xxxx-x:XXXXXXXXXXXX:log-group:/aws/kinesisfirehose/<your_Kinesis_Firehose_delivery_stream_name>:log-stream:*"
            ]
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "kinesis:DescribeStream",
                "kinesis:GetShardIterator",
                "kinesis:GetRecords"
            ],
            "Resource": "arn:aws:kinesis:xx-xxxx-x:XXXXXXXXXXXX:stream/%FIREHOSE_STREAM_NAME%"
        },
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": [
                "arn:aws:kms:region:accountid:key/%SSE_KEY_ARN%"
            ],
            "Condition": {
                "StringEquals": {
                    "kms:ViaService": "kinesis.%REGION_NAME%.amazonaws.com"
                },
                "StringLike": {
                    "kms:EncryptionContext:aws:kinesis:arn": "arn:aws:kinesis:%REGION_NAME%:XXXXXXXXXXXX:stream/%FIREHOSE_STREAM_NAME%"
                }
            }
        }
    ]
}
```
## AWS Lambda Role to access DynamoDB

For the beginning user who has little experience with IAM role, the Kinesis Firehose role can comprise six permissions policies to work with –  

*	AWSLambdaFullAccess – AWS managed policy
*	AmazonDynamoDBFullAccess – AWS managed policy
*	AWSLambdaDynamoDBExecutionRole – AWS managed policy
*	AWSLambdaBasicExecutionRole – AWS managed policy
*	AWSLambdaInvocation-DynamoDB – AWS managed policy
*	awsDynamoDBAccessRole – Managed policy

![Alt text](/images/lambda_role_summ.jpg?raw=true "Lambda Role Summary")

The managed policy `awsDynamoDBAccessRole` comprises the following access permissions –
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:BatchGetItem",
                "dynamodb:BatchWriteItem",
                "dynamodb:DeleteItem",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:UpdateItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:xx-xxxx-x:XXXXXXXXXXXX:table/Likes_Tab"
            ],
            "Condition": {
                "ForAllValues:StringEquals": {
                    "dynamodb:LeadingKeys": [
                        "${www.amazon.com:user_id}"
                    ]
                }
            }
        }
    ]
}
```
The permissions policy of `awsDynamoDBAccessRole` is created from the Access Control tab of the DynamoDB table `Likes_Tab` with all action attributes and using login with Amazon AWS account. Copy the text to create a new policy and attach to the role. 
Below is the screenshot from DynamoDB `Likes_Tab` table Access Control.
 
![Alt text](/images/dynodb_access_policy.jpg?raw=true "DynamoDB Access Control Policy")


## Access Control List for S3 bucket
The S3 bucket permissions comprise full read, write access for the owner AWS account. There is no access provided for other AWS accounts and no public access. The S3 bucket is not for public use but only for private access.
 
![Alt text](/images/S3_bucket_access_policy.jpg?raw=true "S3 bucket Access Policy")


# Testing the Execution of pipeline
Go to the Amazon S3 bucket and there should be a new folder path YYYY/MM/DD/DD created within the prefix (if any provided). In the example, we used `kinesis_firehose_input` as the prefix. Then you can download the file uploaded via AWS pipeline using the `Download` button (see red highlighted).
It will download a file with the name format as <Kinesis Firehose delivery stream name> + <Timestamp> + <unique file identifier>

![Alt text](/images/S3_bucket_file.jpg?raw=true "S3 bucket file")

Note: Based on the `Buffer conditions` set under the Amazon S3 destination in the Firehose delivery stream definition, the output file may take some time to appear under the above-mentioned location in the bucket.
 In case the execution of the pipeline fails due to any reason, an error JSON with the below format will be generated and put into a `processing-failed` folder under the same bucket + prefix (if any)
```
processing-failed/YYYY/MM/DD/XX/<Kinesis Firehose delivery stream name> + <Timestamp> + <unique file identifier>
```
```
{"attemptsMade":4,"arrivalTimestamp":1531212028841,"errorCode":"Lambda.FunctionError","errorMessage":"The Lambda function was successfully invoked but it returned an error result.","attemptEndingTimestamp":1531212106201,"rawData":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","lambdaArn":"arn:aws:lambda:xx-xxxx-xx:XXXXXXXXXXXX:function:lambda_KFH_to_DynoDB:$LATEST"}
```
In parallel, a successful data entry should be visible in the `Like_Tab` DynamoDB table as shown below.

![Alt text](/images/dynodb_data.jpg?raw=true "DynamoDB Data loaded")

# CloudWatch Logs
The CloudWatch logs is seen with the AWS Lambda log printing the below log (see red highlighted parts) once executed successfully.
The log prints the Row that is written to the DynamoDB table along with the response status once writing to the table is finished successfully. It also prints a message while writing to S3 bucket as destination.
## AWS Lambda Log

![Alt text](/images/lambda_log.jpg?raw=true "AWS Lambda log")

