# sample-cmd-task

An example of how to create and run one-off commands on [AWS Fargate](https://aws.amazon.com/fargate/).

This example requires [jq](https://stedolan.github.io/jq/) installed.

The assumption here is that you already have your Docker image in [Amazon ECR](https://aws.amazon.com/ecr/).


### Create an execution role for the ECS task - you may already have one
```
ROLE_NAME=TestEcsExecutionRole
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

TRUST="{ \"Version\": \"2012-10-17\", \"Statement\": [ { \"Effect\": \"Allow\", \"Principal\": { \"Service\": \"ecs-tasks.amazonaws.com\" }, \"Action\": \"sts:AssumeRole\" } ] }"

ROLE_ARN=$(aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document "$TRUST" --output text --query 'Role.Arn')

aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

echo $ROLE_ARN
```

### Build the container
```
$(aws ecr get-login --no-include-email)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
DOCKER_REPO=test

docker build -t test .
docker tag test:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/test:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/test:latest
```

### Register the task definition and run
```
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
DOCKER_REPO=test
CLUSTER=fargate-FargateStack-VGLPTIWDVYXN
FAMILY=one-time

DOCKER_IMAGE=$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$DOCKER_REPO:latest

ROLE_ARN=arn:aws:iam::$ACCOUNT_ID:role/TestEcsExecutionRole

cat container-definitions.json | jq ".containerDefinitions[0].image=\"$DOCKER_IMAGE\"" > /tmp/container-definitions.json

RESPONSE=$(aws ecs register-task-definition \
  --execution-role-arn arn:aws:iam::$ACCOUNT_ID:role/TestEcsExecutionRole \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cli-input-json file:///tmp/container-definitions.json)

REVISION=$(echo $RESPONSE | jq ".taskDefinition.revision")

# You will need to update this with your subnets and security groups
NETWORK=awsvpcConfiguration={subnets=[subnet-05aec45784839acf0,subnet-09c4f73b0caafd290],securityGroups=[sg-0879da6b3e02b6b24],assignPublicIp=DISABLED}

# You only need to run this once - check and see if it's available
aws logs create-log-group --log-group-name one-time 2> /dev/null


aws ecs run-task \
  --cluster $CLUSTER \
  --count 1 \
  --launch-type FARGATE \
  --task-definition $FAMILY:$REVISION \
  --overrides '{ "containerOverrides": [ { "name": "test", "command": [ "python","./another.py" ] } ] }' \
  --network-configuration $NETWORK
```


