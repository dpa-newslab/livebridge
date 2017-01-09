.. _extras:

Howto / Help
============

Use livebridge as a module within another app
---------------------------------------------

.. code-block:: python

    # -*- coding: utf-8 -*-
    import asyncio
    from livebridge.run import main as lb_run

    async def hello_world():
        while 1:
            print("PING")
            await asyncio.sleep(5)

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(hello_world())

    # initialise livebridge
    livebridge = lb_run(loop=loop, control="control-dev.yaml")

    try:
        loop.run_forever()
    finally:
        livebridge.shutdown()
        loop.stop()
        loop.close()

To allow Livebridge to shutdown properly, you should call **livebridge.shutdown()** before stopping \
and closing the event loop.


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

