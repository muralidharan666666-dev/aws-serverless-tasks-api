# AWS Serverless Tasks API

I built this project to get hands-on experience with serverless architecture on AWS. The idea was simple — a task management API where you can create, read, update and delete tasks. No server to manage, no infrastructure to maintain. Just Lambda functions, an API Gateway, and DynamoDB doing all the work.

This was my first time combining Lambda, API Gateway, Cognito, and WAF together in one project. I ran into several real errors along the way which taught me more than any tutorial would have.

---

## What I Built

A REST API with four endpoints:

- `GET /tasks` — fetch all tasks
- `POST /tasks` — create a new task
- `PUT /tasks/{id}` — update a task
- `DELETE /tasks/{id}` — delete a task

Every endpoint requires a valid Cognito JWT token. Requests without a token get rejected at API Gateway before they even reach Lambda.

---

## Architecture

![Architecture Diagram](architecture/architecture.png)

Here is how a request flows through the system:

1. Client sends request to API Gateway endpoint
2. WAF checks the request for common attack patterns
3. API Gateway validates the JWT token via Cognito
4. If the token is valid, it routes to the right Lambda
5. Lambda reads or writes to DynamoDB
6. CloudWatch captures the execution log automatically

---

## AWS Services I Used

**AWS Lambda**
I wrote five separate Lambda functions — one for each operation plus one to generate auth tokens for testing. Each function has its own IAM role with only the permissions it actually needs.

**Amazon API Gateway**
I set up a REST API with two resources: `/tasks` and `/tasks/{id}`. Each resource has the relevant HTTP methods attached and all of them go through the Cognito authorizer before reaching Lambda.

**Amazon DynamoDB**
Single table called `Tasks` with `id` as the partition key. I used uuid4 to generate unique IDs for each task. No schema to worry about and it handled everything quickly.

**Amazon Cognito**
Created a User Pool called `TasksUserPool` with email as the sign-in method. Set up an App Client called `TasksApp` with `ALLOW_USER_PASSWORD_AUTH` enabled. This is what lets Lambda authenticate with a username and password to get back a JWT token.

**AWS WAF**
Created a Web ACL called `TasksAPIProtection` and attached it to the API Gateway `dev` stage. Used AWS Managed Rule Groups which cover SQL injection, XSS, and other common attack patterns without having to configure individual rules manually.

**Amazon CloudWatch**
I did not configure this manually. Lambda automatically creates a log group for each function at `/aws/lambda/functionName`. I checked these during debugging to see what was actually happening inside each invocation.

**AWS IAM**
Created one IAM role called `lambda-dynamodb-role` and attached three policies: `AmazonDynamoDBFullAccess`, `AWSLambdaBasicExecutionRole`, and `AmazonCognitoPowerUser`.

---

## API Endpoints

| Method | Endpoint | Auth Required |
|--------|---------|--------------|
| GET | /tasks | Yes |
| POST | /tasks | Yes |
| PUT | /tasks/{id} | Yes |
| DELETE | /tasks/{id} | Yes |

**Sample create request:**
```json
POST /tasks
Authorization: Bearer eyJraWQiOiJ...

{
    "taskName": "Study AWS Services"
}
```

**Response:**
```json
{
    "message": "Task created successfully",
    "taskId": "8ba9dca2-5a89-4992-9dec"
}
```

---

## Security Setup

I added security at two points in the request path.

**WAF** sits in front of API Gateway and blocks requests that match known attack patterns. I used AWS Managed Rule Groups so I did not have to write individual rules.

**Cognito** is attached as an authorizer on API Gateway. Every method has `TasksAuthorizer` set as the authorization type. Any request without a valid JWT token gets a 401 back immediately.

---

## Project Structure

```
aws-serverless-tasks-api/
├── architecture/
│   └── architecture.png
├── lambda/
│   ├── createTask/
│   │   └── lambda_function.py
│   ├── getTasks/
│   │   └── lambda_function.py
│   ├── deleteTask/
│   │   └── lambda_function.py
│   ├── updateTask/
│   │   └── lambda_function.py
│   └── getAuthToken/
│       └── lambda_function.py
├── screenshots/
├── .gitignore
├── LICENSE
└── README.md
```

---

## Errors I Hit and How I Fixed Them

### Error 1 — Cognito SECRET_HASH

When I tried to authenticate from Lambda, Cognito returned this error:

```
NotAuthorizedException: Client is configured
with secret but SECRET_HASH was not received
```

After researching I found that when an App Client has a secret configured, every auth request needs a SECRET_HASH calculated from the username, client ID and client secret combined. Without it Cognito just rejects the call entirely.

I added that hash calculation to my Lambda function and passed it with the auth request. Authentication worked after that.

---

### Error 2 — FORCE_CHANGE_PASSWORD

After I created a test user in the Cognito console, login kept failing silently. The Lambda was running but `AuthenticationResult` was not in the response at all.

I checked the user in the Cognito console and saw the confirmation status was `Force change password`. Users created from the console are put into this state by default and cannot authenticate until the password is permanently set.

I fixed it using this AWS CLI command in CloudShell:

```bash
aws cognito-idp admin-set-user-password \
--user-pool-id us-east-1_xxxxxxxxx \
--username user@email.com \
--password Password@123 \
--permanent \
--region us-east-1
```

After running that the status changed to `Confirmed` and login worked.

---

### Error 3 — Token Expiry During Testing

About an hour into testing I started getting 401 responses from every endpoint even though my requests looked correct.

The issue was that Cognito ID tokens expire after 1 hour. The token I had copied earlier was no longer valid and API Gateway was rejecting it.

Instead of manually copying tokens every hour I created a separate Lambda called `getAuthToken` that calls Cognito and returns a fresh token. I just run that test in the Lambda console whenever my token expires during testing.

---

## How to Deploy This Yourself

You need an AWS account and AWS CLI configured.

**1. Create DynamoDB table**
- Table name: `Tasks`
- Partition key: `id` (String)
- Leave everything else as default

**2. Create IAM role**
- Role name: `lambda-dynamodb-role`
- Attach these policies:
  - `AmazonDynamoDBFullAccess`
  - `AWSLambdaBasicExecutionRole`
  - `AmazonCognitoPowerUser`

**3. Create Lambda functions**
- Runtime: Python 3.12
- Assign the `lambda-dynamodb-role` role
- Create one function per file in the `lambda/` folder

**4. Set up Cognito**
- Create a User Pool called `TasksUserPool`
- Sign-in method: Email
- Create an App Client called `TasksApp`
- Enable `ALLOW_USER_PASSWORD_AUTH` in the authentication flows

**5. Set up API Gateway**
- Create a REST API
- Add resources `/tasks` and `/tasks/{id}`
- Add GET, POST, PUT, DELETE methods
- Set Lambda proxy integration on each method
- Create a Cognito authorizer and attach it to all methods
- Deploy to a stage called `dev`

**6. Set up WAF**
- Create a Web ACL called `TasksAPIProtection`
- Resource type: Regional (us-east-1)
- Associate it with your API Gateway dev stage
- Add AWS Managed Rule Groups

---

## Testing

I tested all four endpoints using Postman with Bearer Token authentication.

Steps to test:
1. Run the `getAuthToken` Lambda test to get a token
2. Copy the token value from the response
3. In Postman set Auth Type to Bearer Token
4. Paste the token
5. Send your request

| Endpoint | Method | Status |
|---------|--------|--------|
| /tasks | GET | 200 OK |
| /tasks | POST | 201 Created |
| /tasks/{id} | PUT | 200 OK |
| /tasks/{id} | DELETE | 200 OK |

One thing to watch out for — the token expires after 1 hour. If you start getting 401 responses just run `getAuthToken` again to get a fresh one.

---

## What I Learned

A few things I did not know before building this:

**Cognito App Client secrets need special handling.**
If you create a client with a secret enabled every auth call needs a calculated hash included. I did not know this until I hit the error. Next time I would create the client without a secret to keep things simpler.

**Lambda automatically creates CloudWatch log groups.**
I did not configure any logging. Lambda just creates `/aws/lambda/functionName` automatically. I used these logs heavily when debugging the FORCE_CHANGE_PASSWORD issue.

**New Cognito users start in a temporary password state.**
Users created from the AWS Console cannot log in until the password is permanently confirmed. I had to use the AWS CLI to fix this. In a real app users would go through the normal registration flow which handles this automatically.

**WAF managed rules take a few minutes to activate.**
After I attached the WAF to API Gateway it was not instant. There was a short window where requests were still going through before the rules kicked in fully.

---

## Screenshots

All screenshots are in the `/screenshots` folder.

What is there:
- Lambda functions list showing all 5 deployed
- DynamoDB table with sample task items
- API Gateway resource tree showing all endpoints
- Cognito User Pool overview
- WAF Web ACL with associated API Gateway
- CloudWatch log group list for all Lambda functions
- IAM role with attached policies
- Postman screenshots for all four endpoint tests

---


## Author

**Muralidharan M N**

AWS Certified Cloud Practitioner | AWS re/Start Graduate

LinkedIn: https://www.linkedin.com/in/muralidharan-m-n-78a2522b8

GitHub: https://github.com/muralidharan666666-dev

