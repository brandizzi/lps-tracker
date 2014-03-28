To see how to call it:

    $ python lpstracker.py -h
    usage: lpstracker.py [-h] [-r REPOSITORY] [-b BRANCH] [-s SERVER]
                         [-u USERNAME] [-p PASSWORD]
                         LPE-n [LPE-n ...]

    Looks for LPS ticket flags in git history

    positional arguments:
      LPE-n                 LPE issues whose related LPS issues should be found

    optional arguments:
      -h, --help            show this help message and exit
      -r REPOSITORY, --repository REPOSITORY
                            Path to Git repository
      -b BRANCH, --branch BRANCH
                            Branch to be searched
      -s SERVER, --server SERVER
                            JIRA Server URL
      -u USERNAME, --username USERNAME
                            JIRA user name
      -p PASSWORD, --password PASSWORD
                            JIRA Password

For example:

    $  python lpstracker.py -u<user> -p<pwd> -r /home/brandizzi/liferay-portal LPE-10001  LPE-10002  LPE-10009  LPE-10010

Depends on modules 'gitpython' and 'jira-python'. They can be installed with
easy_install or pip.
