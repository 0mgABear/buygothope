Project: BuyGotHope (Loosely Translated from 有没有希望)

Idea:
Telegram Bot that can either be subscribed to or added to groups to check the next jackpot and draw amount.
If draw amount exceeds a certain pre-set amount, it will include a funny line like "有买有希望" (buy got hope), or any other funny quotes.

Planned Technical Implementation Steps:

1. Test script locally.
2. Upload it to AWS Lambda and validate.

Challenges Faced:

1. ZIP file uploaded to AWS did not work.
2. Dockerising had many difficulties as listed below:

a.

```
 module 'chromium' has no attribute 'executable_path'
TargetClosedError: Browser.new_page: Target page, context or browser has been closed
```

b.

```
GLIBC_2.27 not found
GLIBC_2.28 not found
```

c.

```
exec: "awslambdaric": executable file not found in $PATH
Runtime API server failed to listen
AWS_LAMBDA_RUNTIME_API missing
```

d.

```
Unable to import module 'lambda_function'
```

e. Cold Start

3. Using public ECR instead of private ECR for free storage

Solutions:

1. Dockerise code with all dependencies.
2. a. Added Lambda-compatible Chromium flags
   b. Used a different base image

```
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy
```

c. Installed awslambdaric and changed command to

```
CMD ["python3", "-m", "awslambdaric", "lambda_function.lambda_handler"]
```

d. Changed working directory

```
WORKDIR /var/task
COPY lambda_function.py .
```

e. Caching Chromium in /tmp

3. Grant public ECR access to existing AWS IAM role with the following methods:
   Method 1:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ECRPublicAccess",
            "Effect": "Allow",
            "Action": [
                "ecr-public:*",
                "sts:GetServiceBearerToken"
            ],
            "Resource": "*"
        }
    ]
}
```

Method 2: Add proper AWS-Managed Policy
IAM --> Users --> (Username) --> Add permissions --> Attach Policies Directly
Permission to use in this case: AmazonElasticContainerRegistryPublicFullAccess
