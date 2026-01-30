# Project: Got Buy Got Hope

(Loosely Translated from 有买有希望)

Idea:
Telegram Bot that can either be subscribed to or added to groups to check the next jackpot and draw amount.
If draw amount exceeds a certain pre-set amount, it will include a funny line like "有买有希望" (buy got hope), or any other funny quotes.

Planned Technical Implementation Steps:

1. Test script locally.
2. Upload it to AWS Lambda and validate.
3. Telegram Implementation
   a. Integtrate with Telegram API
   b. Validate with private chat - ensure that it is working
   c. Validate bot functionality in a channel

Branches Overview:

1. Main - Browserless + Playwright + Lambda (current, working)
2. playwright-docker-lambda - Full Playwright + Chromium in Lambda (deprecated)

Intitial Approach: Dockerise Playwright and try to run it entirely within Lambda. Docker Image was hosted on Amazon ECR.
Although it was working, it would not be a fully free approach, costing about ~$0.02USD/month.
Albeit marginal, I opted for a workaround (Browserless) for a fully-free solution so that this solution can run in perpetuity.

At the time of development (December 2025), Browserless offered a free tier that was adequate for low-frequency, personal automation use cases such as this project.

Challenges Faced:

1. Docker Desktop produced an OCI image index (multi-arch), which AWS Lambda does not support.

Solution:

- Force linux/amd64 and disable provenance & SBOM
  Error Message:

```
The image manifest, config or layer media type for the source image 383675638173.dkr.ecr.ap-southeast-1.amazonaws.com/toto-browserless-lambda@sha256:9e750709f1c44b00b3142cdb44628d55dfac072ede6330f9bb983a20bd5333ca is not supported.
```

Solution:
a. changing docker file to:

```
CMD ["python", "-m", "awslambdaric", "lambda_function.lambda_handler"]
```

b. Building docker image differently via the command below:

```
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -t 383675638173.dkr.ecr.ap-southeast-1.amazonaws.com/toto-browserless-lambda:latest \
  --push .
```

2. Testing Lambda Error Message:

```
{
  "errorMessage": "2025-12-21T06:14:47.123Z 9eef0a0b-f015-40aa-995a-83faae5f105a Task timed out after 3.01 seconds"
}
```

Solution: Increase timeout and Memory. Successful.
![Lambda execution success](screenshots/TEST_SUCCESS.png)

Completion Date: 22 Dec 2025

The bot will have a daily reminder at 12PM about when is the next TOTO Jackpot.

## Learning Points:

1. Login Docker to ECR

```
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 383675638173.dkr.ecr.ap-southeast-1.amazonaws.com

```

2. Building and Pushing Docker Image

```
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -t 383675638173.dkr.ecr.ap-southeast-1.amazonaws.com/toto-browserless-lambda:latest \
  --push .
```

3. Update Lambda to new image

```
aws lambda update-function-code \
  --function-name <YOUR_LAMBDA_FUNCTION_NAME> \
  --image-uri 383675638173.dkr.ecr.ap-southeast-1.amazonaws.com/toto-browserless-lambda:latest
```

## Updates

1. Quality of Life Update
   Date Check. Bot runs everyday, will perform a check if the next draw date is the date of execution.
   If so, bot will ping that the draw is "Tonight, XX timing" rather than the generic Next Draw: XX Day, XX Timing.

2. Performance Enhancements

Although the site data is loaded dynamically using JS, some of the data is loaded into identifable DOM elements with labels and classes.
With the aid of this, improvements can be made to retrieve the data via such labels instead of a REGEX search, which may not be as robust and accurate.
This also avoids unnecessary full page text processing.

3. Introduction of Witty Comment

Using Gemini API (as there is a small free tier), we can generate a comment to "encourage" people to buy the TOTO Jackpot.

4. Introduction of Mode 2: Results Mode

This was a requested feature, which is also a key quality-of-life update. At date of running, if there is a result, the bot will also check for results.
It will return the winning numbers, additional number, number of winner(s) and details of the winning ticket(s).

5. Quality of life change: Update Telegram Message when there are no winners instead of returning:
   `Group 1: - each (- winner(s))`
   which is not so aesthetic.

6. Improve robustness of Gemini Generation Logic.
   Encountered a transient error on 23/01/2026 with the folllowing logs:

```
503 Server Error: Service Unavailable for url: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent
```

Further local testing revealed that it was working, re-testing by invoking directly on AWS Lambda also generated the Gemini comment.
Preliminary conclusions: one-off errror.

Fix taken (retry mechanism) to improve the robustness against such errors.

7. Improvement of Scheduling for better and more reliable results generation.
   Creation of one-off EventBridge schedule via code instead of a daily 10:30PM Cron EventBridge Schedule.
