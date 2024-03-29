# Capacity Tier S3 Setup w/o Immutability

[Veeam Capacity Tier](https://helpcenter.veeam.com/docs/backup/vsphere/capacity_tier.html) expands the scale-out backup repository abilities and allows you to store backup data in cloud-based object storage or S3-Compatible on-premises storage.

This CloudFormation Template deploys the required AWS constructs to add an object storage backup repository **without Immutability** to Veeam Backup & Replication. It performs the following actions:

* Creates an S3 Bucket
* Creates an IAM User
  * User only has minimal access to the newly created S3 Bucket
* Template `Outputs` provide the following information:
  * **Region:** AWS Region
  * **User:** Newly created IAM user
  * **AccessKey:** Access key ID of new user
    * [Used for Veeam Credentials](https://helpcenter.veeam.com/docs/backup/vsphere/amazon_repository_account.html)
  * **SecretKey:** Secret access key of new user
    * [Used for Veeam Credentials](https://helpcenter.veeam.com/docs/backup/vsphere/amazon_repository_account.html)
  * **VeeamS3Bucket:** Newly created S3 bucket

## Usage

Below is a quick-create link you can use to easily deploy this CloudFormation template in your environment:

[![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?templateURL=https://veeamhub-public.s3.amazonaws.com/veeam-aws-cloudformation/veeam-backup-and-replication/capacity-tier-s3-standard/cf-veeam-s3-standard.yaml&stackName=veeam-s3-standard)

If you'd like to view/edit the source code prior to deploying it in your environment, you can access the source code [here](cf-veeam-s3-standard.yaml).
