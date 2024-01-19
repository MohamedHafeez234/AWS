#!/bin/bash

#export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
#export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
#export AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION

# if ENVs for the aws configure are already set no need to initialize again

#aws configure sso --profile $profile_name
#If the SSO is configured, we can run these above commands.

previous_time=$(date -d '30 days ago' --utc +%Y-%m-%dT%H:%M:%S)
expired_objects=()

# Find S3 buckets whose names end with ".test"
buckets=$(aws s3 ls | grep '\.test$' | awk {'print $3'}) 


for bucket_name in $buckets; do
    echo "Processing bucket: $bucket_name"
    objects=$(aws s3api list-objects --bucket "$bucket_name" --query "Contents[?ends_with(Key, '.xml') && LastModified<'$previous_time' || null].Key" --output text)
    #echo $objects # prints all objects which expired before 30days of .xml

    for key in $objects; do
      # Expire the object
      aws s3api delete-object --bucket $bucket_name --key "$key"
      echo "Expired: $key"
    done

done
