.. _extras:

Howto / Help
============


IAM policy for running on Amazon AWS
------------------------------------

To run Livebridge on Amazon AWS, following IAM rule can be used:

.. code-block:: json

    {
        "Version": "2012-10-17",
        "Statement": [
        {
                "Effect": "Allow",
                "Action": "s3:*",
                "Resource": [
                    "arn:aws:s3:::S3_CONFIG_BUCKET/*"
                ]
            },
            {
                "Action": [
                    "dynamodb:*"
                ],
                "Effect": "Allow",
                "Resource": [
                    "arn:aws:dynamodb:eu-central-1:AWS_ACCOUNT_ID:table/*",
                    "arn:aws:dynamodb:eu-central-1:AWS_ACCOUNT_ID:table/*/index/*"
                ]
            },
            {
                "Action": [
                    "dynamodb:ListTables"
                ],
                "Effect": "Allow",
                "Resource": [
                    "*"
                ]
            },
        {
                "Sid": "Stmt1468584281000",
                "Effect": "Allow",
                "Action": [
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                    "sqs:GetQueueUrl",
                    "sqs:ListQueues",
                    "sqs:ReceiveMessage",
                    "sqs:PurgeQueue"
                ],
                "Resource": [
                    "arn:aws:sqs:eu-central-1:AWS_ACCOUNT_ID:*"
                ]
            }
        ]
    }

