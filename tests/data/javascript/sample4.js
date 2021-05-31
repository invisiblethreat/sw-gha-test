import ajax from './small-ajax';

const CLOUD_PROVIDER_ACCOUNTS_URL = '/up-api/cloud-provider-accounts';
const CLOUD_ACCOUNT_RESOURCES = '/up-api/cloud-account-resources';
const CLOUD_ACCOUNT_COUNTS_RESOURCES = '/amazon/resources';

export const fetchAccounts = () => ajax.get(CLOUD_PROVIDER_ACCOUNTS_URL);

export const createAccount = ({accountName, authData, accountType}) => ajax.post(CLOUD_PROVIDER_ACCOUNTS_URL, {
    accountName,
    authData,
    accountType
});

export const updateAccount = (accountId, {accountName, authData, accountType}) => ajax.put(`${CLOUD_PROVIDER_ACCOUNTS_URL}/${accountId}`, {
    accountName,
    authData,
    accountType
});

export const deleteAccount = (id) => ajax.del(`${CLOUD_PROVIDER_ACCOUNTS_URL}/${id}`);

export const updateResources = ({accountId, resources}) => ajax.patch(CLOUD_ACCOUNT_RESOURCES, {accountId, resources});

/*
@oas [get] /amazon/resources/{arn}/{externalId}
{
    "tags": ["aws"],
    "description": "Get resources for the AWS account",
    "operationId": "awsResources",
    "parameters": [
        {
            "name": "arn",
            "in": "path",
            "description": "AWS ARN",
            "required": true,
            "schema": {
                "type": "string"
            }

        },
        {
            "name": "externalId",
            "in": "path",
            "description": "AWS External ID",
            "required": true,
            "schema": {
                "type": "string"
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Resources",
            "content": {
                "text/html; charset=utf-8": {
                    "example": "{\"<awsAccountID>\":{\"ap-northeast-1\":{\"ApplicationELB\":{},\"EC2\":{},\"NetworkELB\":{},\"RDS\":{},\"S3\":{\"bucketName\":true}}}"
                }
            }
        }
    }
}
*/

export const updateCountsResources = ({arn, role, externalID}) => ajax.get(`${CLOUD_ACCOUNT_COUNTS_RESOURCES}/${arn}/${role}/${externalID}`);