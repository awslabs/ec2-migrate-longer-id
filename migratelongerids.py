#!/usr/bin/env python
# Copyright 2016. Amazon Web Services, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Imports section. Import SDK and required libraries.
import argparse
import threading
import sys
from time import sleep
import logging
from queue import Queue
from botocore.client import Config
# try fail-able imports and imports with versioning requirements
try:
  import boto3
except ImportError:
    raise ImportError("Unable to import boto3. Please make sure you have read the README.md and run"
                      " pip install boto3")

try:
    boto3.__version__ < "1.2.1"
except EnvironmentError:
    raise EnvironmentError("version of boto3 is too low. Please run:\npip install -U boto3 to "
                           "upgrade your version of boto3 to a version newer than 1.2.1.")

from botocore.exceptions import ClientError

# version of python that this is written for. This should also run on higher versions of python,
# such as 3.5

MINPYTHONVERS = (2, 7)

if sys.version_info < MINPYTHONVERS:
    sys.exit('Need Python version >= %s' % MINPYTHONVERS)

# Globally Defined Variables/Constants
MAXTHREADS = 50
CONST_INDEX = 0
DELAY = 2
maxretry = 10
SECONDS = .1
MAXRETRY = 10
accountnumberindex = 4
clienterrormessage = """failed to successfully execute API call within counter limit. Please try this
                      again later as there may be something larger going on. Please check the
                      service health dashboard for any ongoing events:
                      http://status.aws.amazon.com"""
log = logging.getLogger(__name__)
return_message = logging.StreamHandler(sys.stdout)
return_message.setFormatter(logging.Formatter('%(message)s'))
return_message.setLevel(logging.INFO)
log.addHandler(return_message)
log.setLevel(logging.INFO)


# End Globally Defined Variables


# Function Definition section
# Staged function
def exception_handler():
    """This function hasn't been integrated yet. This WILL be what handles sleep and exception
    handling code. This call needs to be inserted into every Try, except block in the script."""
    log.info(("error code:", clierror.response['ResponseMetadata']['HTTPStatusCode'],
              "\nrequest ID:", clierror.response['ResponseMetadata']['RequestId']))
    log.info(("sleep for:", counter * DELAY))
    sleep(counter * DELAY * SECONDS)
# End Staged function


def call_status(regions, resource_number, resources):
    """This function is intentionally linear/sequential for now. Later, it may be re-done to
    thread and lock stdout so that regions are printed as they are completed. Additionally, this
    will eventually pull in logging functionality to facilitate cleaning up the screen."""
    for k in regions:
        describeid(k, resource_number, resources)


def convert(clientboolean, threadqueue):
    """This function is the heart and soul of the app. This creates a creates threads, then pops
    an item from the queue to run a function in the thread."""
    while not threadqueue.empty():

        if threading.active_count() < MAXTHREADS:
            region, user, arn = threadqueue.get()
            worker = threading.Thread(target=threadedmodify, args=(region, user, arn,
                                      clientboolean))
            worker.start()


def selfconvertqueue(regions, id_resources):
    """This function creates a special queue to run via convert such that only the current calling
     arn is modified. Either reverted or converted."""

    tqueue = Queue()
    sts_client = boto3.client('sts')
    iam_client = boto3.client('iam')
    calling_arn = ''

    ident = sts_client.get_caller_identity()['UserId'].split(":")[CONST_INDEX]
    listroles = iam_client.list_roles()
    listusers = iam_client.list_users()
    for key in listroles['Roles']:
        if key['RoleId'] == ident:
            calling_arn = key['Arn']
    for key in listusers['Users']:
        if key['UserId'] == ident:
            calling_arn = key['Arn']

    '''run a loop to create the queue off of the identity and replace the previous threadqueue value. This only runs a single arn'''
    if not calling_arn == '':
        for region in regions:
            for resource in id_resources:
              tqueue.put((region, calling_arn, resource))

    return tqueue


# Former getregions code:
def getregions():
    region_client = boto3.client('ec2')

    counter = 1

    while True:
        try:
            region_response = region_client.describe_regions()
        except ClientError as clierror:
            log.info(("error code:", clierror.response['ResponseMetadata']['HTTPStatusCode'],
                      "\nrequest ID:", clierror.response['ResponseMetadata']['RequestId']))
            log.info(("sleep for:", counter * DELAY))
            sleep(counter * DELAY * SECONDS)
            if counter <= MAXRETRY:
                counter += 1
                continue
            else:
                break
        break

    regions = [region['RegionName'] for region in region_response['Regions']]

    return regions
# End getregions functions


# Former getiam code:
def getuserandrole():
    arn_index = 0
    account_index = 4
    """gets IAM users and roles from the account and creates an ARN list to be used when creating a
     queue"""

    iam_client = boto3.client('iam')

    # section gets all roles for the account and adds them to a list that is to be returned to the
    # main program for processing
    counter = 1
    while True:
        try:
            iam_roles_response = iam_client.list_roles()
            iam_users_response = iam_client.list_users()
        except ClientError as clierror:
            log.info(("error code:", clierror.response['ResponseMetadata']['HTTPStatusCode'],
                  "\nrequest ID:",clierror.response['ResponseMetadata']['RequestId']))
            log.info(("sleep for:", counter * DELAY))
            sleep(counter * DELAY * SECONDS)
            if counter <= MAXRETRY:
                counter += 1
                continue
            else:
                break
        break

    arn_list = [users['Arn'] for users in iam_users_response['Users']]
    arn_list += [roles['Arn'] for roles in iam_roles_response['Roles']]

    # add root arn to list manually since it doesn't show up in the list. Maybe come back and add
    # the arn in a more elegant way later down the road. For now this is just part of the PoC
    root_arn = "arn:aws:iam::" + arn_list[arn_index].split(':')[account_index] + ":root"
    arn_list.append(root_arn)
    return arn_list
# End former getiam code


# Former modifyid code
def idresourcelist():
    """this gets the list of resources that can currently be modified to the longer instance
    format. This currently does not have any interaction and should always return the most
    up-to-date information about what resources have moved to the longer format."""

    id_client = boto3.client('ec2')
    counter = 1
    while True:
        try:
            id_client_response = id_client.describe_id_format()
        except ClientError as clierror:
            log.info(("error code:", clierror.response['ResponseMetadata']['HTTPStatusCode'],
                  "\nrequest ID:", clierror.response['ResponseMetadata']['RequestId']))
            log.info(("sleep for:", counter * DELAY))
            sleep(counter * DELAY * SECONDS)
            if counter <= MAXRETRY:
                counter += 1
                continue
            else:
                log.info((clienterrormessage))
            break
        break
    identresources = [resource['Resource'] for resource in id_client_response['Statuses']]
    return identresources


def describeid(awsregion, arn, ident_resources):
    """This does the output for all IAM ARNs and Resources in a single region. This is called by
    another program that builds the total list based on the regions. This is called from
    call_status."""

    id_client = boto3.client('ec2', region_name=awsregion)

    # desired behavior: 1.)loop over IAM resources
    # 2.)nested loop over the identresources
    region_string = awsregion + ":"
    log.info(region_string)

    for usersandroles in arn:
        for resourcetype in ident_resources:
            counter = 1
            while counter <= MAXRETRY:
                try:
                    id_client_response = id_client.describe_identity_id_format(Resource=resourcetype,
                                                                            PrincipalArn=usersandroles)
                except ClientError as clierror:
                    log.info(("error code:", clierror.response['ResponseMetadata']['HTTPStatusCode'],
                              "\nrequest ID:", clierror.response['ResponseMetadata']['RequestId']))
                    log.info(("sleep for:", counter * DELAY * SECONDS))
                    sleep(counter * DELAY * SECONDS)
                    if counter <= MAXRETRY:
                        counter += 1
                    else:
                        log.info(clienterrormessage)
                        sys.exit(1)
                break
            for line in id_client_response['Statuses']:
                log.info(('%-100s: %-12s: %-20s' % (usersandroles, line['Resource'],
                          line['UseLongIds'])))

    log.info("")


def tqueue(awsregion, arn, identresources):
    """This function has the purpose of setting up the thread queue to pull threads from when
    making the api calls. """

    thread_queue = Queue()
    for region in awsregion:
        for resourcetype in identresources:
            thread_queue.put((region, arn, resourcetype))

    return thread_queue


def threadedmodify(awsregion, arn, resourcetype, clientbool):
    client_conf = Config(user_agent_extra="longer_id_migration_support_tool/1.0")
    id_client = boto3.client('ec2', region_name=awsregion, config=client_conf)


    counter = 1
    while True:
        try:
            id_client_response = id_client.modify_identity_id_format(Resource=resourcetype,
                                                                  PrincipalArn=arn,
                                                                  UseLongIds=clientbool)
        except ClientError as clierror:
            log.info(("error code:", clierror.response['ResponseMetadata']['HTTPStatusCode'],
                  "\nrequest ID:", clierror.response['ResponseMetadata']['RequestId']))
            log.info(("sleep for:", counter * DELAY * SECONDS))
            sleep(counter * DELAY * SECONDS)
            if counter <= MAXRETRY:
                counter += 1
                continue
            else:
                log.info((clienterrormessage))
                break
        convert_string = awsregion + " : " + id_client_response['ResponseMetadata']['RequestId']
        log.info(convert_string)
        break
    return id_client_response
# End former modifyid code

# End Function Definitions section

# Set up function calls depending upon Arguments selected
def main():
    """This is the main function that drives the appliction. If this is imported into other python code,
    this section won't be executed when the import occurs. Ways to use the main program:
    --status
    --convertonly
    --convertself
    --revert
    --revert --status
    --revert --convertself --convertonly
    --convertself --status
    --convertself --convertonly    --status
    --convertonly
    --convertself
    --revert
    --revert --status
    --revert --convertself --convertonly
    --convertself --status
    --convertself --convertonly
    [--profile]"""

    #Variables:
    clibool = True

    # ArgParse section. Many thanks to JoshF for code snippets to look at and understand argparse
    # better. Args currently are: Status, Revert, and Convertonly. Revert is the "oops" fallback in
    # case something goes wrong after the deploy. Eventually, Revert will be more intelligent. Now, it
    # just reverses everything to shorter IDs.

    parser = argparse.ArgumentParser(description='This tool converts accounts to the new longer ID '
                                                 'format as long as the IAM user/role you are using is'
                                                 ' Administrator level in IAM')
    parser.add_argument('--status', action='store_true', help='presents status of all your IAM '
                                                              'resources and exits.')
    parser.add_argument('--revert', action='store_true', help='revert longer ID format to its former '
                                                              'state')
    parser.add_argument('--convertonly', action='store_true', help='This converts the account, but '
                                                                   'does not print a status at the '
                                                                   'end.')
    parser.add_argument('--convertself', action='store_true', help='This converts the single ARN in'
                                                                   'all regions.')
    parser.add_argument('--profile', help='Use different profile credentials')

    args = parser.parse_args()

    boto3.setup_default_session(profile_name=args.profile)

    arn = 'all'
    regions = getregions()
    usersandids = getuserandrole()  # This is only useful for status calls

    idresources = idresourcelist()
    threadqueue = tqueue(regions, arn, idresources)

    """Main program logic. Everything else sets up for this. The goal of the code here is to try
    to allow more functionality. Status should and can be called along with other functions.
    Convertself should only convert for the arn of the role/user that is calling the program.
    Convertonly should not print a status but should run either by itself OR with Convertself. If
    status is the only arg, it should only print the status."""

    if args.revert:
        clibool = False

    if args.convertself:
        threadqueue = selfconvertqueue(regions, idresources)

    if len(sys.argv) > 2 and args.convertonly and not args.convertself and not args.convertonly:
        log.info("invalid selection. convertonly can ONLY be used as the sole argument or with "
                 "convertself")
        sys.exit(1)

    if args.convertself and args.convertonly and len(sys.argv) > 3 and not args.revert:
        log.info("invalid selection. convertonly + convertself can not have additional args,"
                 " unless used with revert.")
        sys.exit(1)

    if args.convertonly:
        convert(clibool, threadqueue)
        sys.exit(0)

    if args.status and len(sys.argv) <= 2:
        call_status(regions, usersandids, idresources)
        sys.exit(0)

    if len(sys.argv) >= 1:
        convert(clibool, threadqueue)
        call_status(regions, usersandids, idresources)
        sys.exit(0)

    if len(sys.argv) > 1 and not args.convertonly:
        convert(clibool, threadqueue)
        sys.exit(0)

    log.info("You reached this in error. Something went wrong. Please report this incident.")

if __name__ == "__main__":
    main()
