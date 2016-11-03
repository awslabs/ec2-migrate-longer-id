#ec2-migrate-longer-id
migratelongerids.py

#Overview
This project was designed due to the current move AWS has announced regarding switching resource IDs to a longer format.
The goal of this project is to enable faster and easier conversion of entire accounts to the new longer ID format.

Once adequate testing has been done with an IAM user, region, IAM role, or any combination of the previously mentioned
parameters, you can use this tool to move the rest of your account (or other accounts such as testing, UAC, and PROD)
over to the new format.

This tool can show you the status of your account. It will go through all regions with the `--status` flag and return
the current status of each IAM ARN (user or role) and the root user and return True or False for each of the longer
ID types currently. Those id types are (as of the time of this writing):  
`Instance`  
`Reservation`  
`Snapshot`  
`Volume`  

It currently spins up 50 threads and the threads pull from a queue that has been populated by iterating over regions,
IAM roles, IAM users, the root user, and each resource type. This queue is then used by the threads to make an API call
and modify the exact resource. Once all threads are completed, the program continues with any additional functions
(such as status).  

The program will wait for each thread to complete before continuing any additional functions.

#Requirements:
You need to be running python 2.7 to run this application. This assumes you also have the awscli installed and
configured. Alternatively, you can add the following files:  
`~/.aws/credentials`  
`~/.aws/config`  
using the same format you saw  
To use this program, you need to have the following modules installed:  
External dependencies
---------------------

boto3, python2.7, git, future

You can install these by using the proper command depending on your OS:  
Windows:  
`C:\> easy_install pip` (If you don't already have pip installed)  
`C:\> pip install virtualenvwrapper-win`  
`C:\> mkproject migrate_to_longer_ids`  
`C:\> workon migrate_to_longer_ids`  
`C:\> source venv/bin/activate`  
`C:\> pip install boto3 future`  

Linux/Mac OS X (depending on your distro/OS, your steps may vary slightly):

RHEL/CentOS/EL 6 and RHEL/CentOS/EL 7:  
`sudo yum install python-virtualenv`  
`virtualenv -p /usr/bin/python2.7 venv`  
`source venv/bin/activate`  
`pip install boto3 future`  

Debian/Ubuntu:  
`apt-get install python-virtualenv`  
`virtualenv -p /usr/bin/python2.7 venv`  
`source venv/bin/activate`  
`pip install boto3 future`  

*NOTE*: If you wish to pull this from github, you likely want/need git installed to get the files. Please follow instructions
to install git here:  
https://git-scm.com/book/en/v2/Getting-Started-Installing-Git  
If you use mac, I recommend using homebrew instead of the instructions above. You can get brew here:  
http://brew.sh/

Also, with virtualenv, you can reference this site for basic usage if you have additional questions:
http://docs.python-guide.org/en/latest/dev/virtualenvs/

Then, you can git clone the package onto your machine and then run the code from where you saved your code. 

#Usage:
Calling the program by itself will simply convert your account and its IAM roles/users (if you have the proper IAM permissions),
print status, and exit. You can achieve this by:  
`./migratelongerids.py`  
If you would like the status of your account, you can perform the following:  
`./migratelongerids.py --status`  
If you would like to revert to the former shorter ID format due to something going wrong, you can execute this command:  
`./migratelongerids.py --revert`  
If you want to just run a convert and not do a status update, you can execute this:  
`./migratelongerids.py --convertonly`  
If you want to just convert YOUR user/role, then you can use the convertself feature:  
`./migratelongerids.py --convertself`  

You can Combine Status to be used with revert and convertself and will output the status AFTER you run the convert:  
`./migratelongerids.py --convertself --status` OR  
`./migratelongerids.py --revert --status`  

You can use the optional --profile PROFILE to specify a different profile to use from the ~/.aws/credentials file

All possible usage combinations:  
`--status`  
`--convertonly`  
`--convertself`  
`--revert`  
`--revert --status`  
`--revert --convertonly`  
`--revert --convertself --convertonly`  
`--convertself --status`  
`--convertself --convertonly` 
