#!/usr/bin/env python

import os.path

import git

class GitSearcher(object):
    """
    Search commits for references for specific JIRA tickets.
    """

    def __init__(self, repository=os.path.curdir, branch=None):
        self.repository = git.Git(repository)
        self.branch = branch

    def get_commits(self, tickets):
        """
        Find all commits with the listed tickets.

        Usage:

        >>> GitSearcher().get_commits(['LPS-32', 'LPS-33'])
        ['4748d69 LPS-33 Removing example', '5fa1862 LPS-32 Just an example']

        Giving repository (current dir by default):

        >>> GitSearcher(repository='.').get_commits(['LPS-32', 'LPS-33'])
        ['4748d69 LPS-33 Removing example', '5fa1862 LPS-32 Just an example']

        Giving branch (master by default):

        >>> GitSearcher(branch='master').get_commits(['LPS-32', 'LPS-33'])
        ['4748d69 LPS-33 Removing example', '5fa1862 LPS-32 Just an example']
        """
        flags = self._get_ticket_flags(tickets)
        commits = self.repository.log(['--oneline'] + flags).split('\n')

        return commits

    def _get_ticket_flags(self, tickets):
        """
        Generate the expected flags for 'git log'

        Usage:

        >>> GitSearcher()._get_ticket_flags(['LPS-1', 'LPS-2'])
        ['--grep=LPS-1', '--grep=LPS-2']

        Also, when it has a branch

        >>> GitSearcher(branch='6.2.x')._get_ticket_flags(['LPS-1', 'LPS-2'])
        ['--grep=LPS-1', '--grep=LPS-2', '6.2.x']
        """
        flags = ['--grep={}'.format(ticket) for ticket in tickets]

        if self.branch:
            flags.append(self.branch)

        return flags

import itertools

import jira.client

LIFERAY_JIRA_SERVER = 'http://issues.liferay.com'
LPS = 'LPS'

class JIRASearcherException(Exception):

    def __init__(self, msg=''):
        Exception.__init__(self, msg)

class JIRASearcher(object):
    def __init__(self, server=LIFERAY_JIRA_SERVER, username=None, password=None,
                access_token=None, access_token_secret=None, consumer_key=None,
                key_cert=None):

        self.server = server

        self.basic_auth_parameters = self._get_basic_auth_parameters(username,
                password)
        self.oauth_parameters = self._get_oauth_parameters(access_token,
                access_token_secret, consumer_key, key_cert)
        self.jira = None

    def get_issue(self, issue):
        """
        Get the issue by its key.

        >>> js = JIRASearcher(username=file('.jira_username').read(),
        ...    password=file('.jira_password').read())
        >>> js.connect()
        >>> issue = js.get_issue('LPE-10001')
        >>> issue
        <JIRA Issue: key=u'LPE-10001', id=u'147265'>

        If a issue is given, return it:

        >>> js.get_issue(issue) == issue
        True

        >>> js.close()
        """
        return (issue
                if isinstance(issue, jira.client.Issue)
                else self.jira.issue(issue))

    def get_issues(self, issues):
        """
        Get the issues by their keys.

        >>> js = JIRASearcher(username=file('.jira_username').read(),
        ...    password=file('.jira_password').read())
        >>> js.connect()
        >>> js.get_issues(['LPE-10001', 'LPE-10002'])
        [<JIRA Issue: key=u'LPE-10001', id=u'147265'>, <JIRA Issue: key=u'LPE-10002', id=u'147267'>]
        >>> js.close()
        """
        return [self.get_issue(issue) for issue in issues]

    def get_related_issues(self, issue, project=LPS):
        """
        Get the keys of issues related to the given one which have the given
        project.

        >>> js = JIRASearcher(username=file('.jira_username').read(),
        ...    password=file('.jira_password').read())
        >>> js.connect()
        >>> js.get_related_issues('LPE-10001')
        [u'LPS-41798']
        """
        issue = self.get_issue(issue)

        issue_links = issue.fields.issuelinks
        raw_links = [il.raw for il in issue_links]
        inward_issues = [rl['inwardIssue'] for rl in raw_links]

        return [ii['key']
                for ii in  inward_issues
                if not project or ii['key'].startswith(project)]

    def get_related_issues_dict(self, issues, project=LPS):
        """
        Get the keys of issues related to the given ones which have the given
        project.

        >>> js = JIRASearcher(username=file('.jira_username').read(),
        ...    password=file('.jira_password').read())
        >>> js.connect()
        >>> js.get_related_issues_dict(['LPE-10001', 'LPE-10002'])
        {u'LPE-10002': [u'LPS-41981'], u'LPE-10001': [u'LPS-41798']}

        >>> js.close()
        """
        issues = self.get_issues(issues)

        return {
            issue.key: self.get_related_issues(issue.key, project)
            for issue in issues
        }

    def get_related_issues_set(self, issues, project=LPS):
        """
        Get the keys of issues related to the given ones which have the given
        project, as a set.

        >>> js = JIRASearcher(username=file('.jira_username').read(),
        ...    password=file('.jira_password').read())
        >>> js.connect()
        >>> js.get_related_issues_set(['LPE-10001', 'LPE-10002'])
        set([u'LPS-41798', u'LPS-41981'])

        >>> js.close()
        """
        related_issues = self.get_related_issues_dict(issues, project).values()
        return set(itertools.chain(*related_issues))

    def connect(self):
        self.jira = jira.client.JIRA(**self._get_jira_parameters())

    def close(self):
        self.jira = None

    def _get_jira_parameters(self):
        """
        Get a dict what contains parameters for jira.client.JIRA() constructor.
        If not is given to JIRASearcher() constructor, returns some sensible
        parameters:

        >>> JIRASearcher()._get_jira_parameters()
        {'options': {'server': 'http://issues.liferay.com'}}
        >>> JIRASearcher(server='http://jira.atlassian.com')._get_jira_parameters()
        {'options': {'server': 'http://jira.atlassian.com'}}

        If given, returns parameters for basic auth...

        >>> JIRASearcher(username='foo', password='bar')._get_jira_parameters()
        {'options': {'server': 'http://issues.liferay.com'}, 'basic_auth': ('foo', 'bar')}

        ... and OAuth:

        >>> JIRASearcher(access_token='d87f3hajglkjh89a97f8',
        ...    consumer_key='jira-oauth-consumer',
        ...    access_token_secret='a9f8ag0ehaljkhgeds90',
        ...    key_cert='... some data here ...')._get_jira_parameters()
        {'oauth': {'access_token': 'd87f3hajglkjh89a97f8', 'consumer_key': 'jira-oauth-consumer', 'access_token_secret': 'a9f8ag0ehaljkhgeds90', 'key_cert': '... some data here ...'}, 'options': {'server': 'http://issues.liferay.com'}}

        Except, of course if you:

          * forget some basic auth parameter;

            >>> JIRASearcher(username='foo')._get_jira_parameters()
            Traceback (most recent call last):
              ...
            JIRASearcherException: Some, but not all, parameters passed to basic authentication

          * forget some oauth parameter; or

            >>> JIRASearcher(access_token='d87f3hajglkjh89a97f8',
            ...    access_token_secret='a9f8ag0ehaljkhgeds90',
            ...    key_cert='... some data here ...')._get_jira_parameters()
            Traceback (most recent call last):
              ...
            JIRASearcherException: Some, but not all, parameters passed to OAuth

          * give parameters for more than one auth method:

            >>> JIRASearcher(username='foo', password='bar',
            ...    access_token='d87f3hajglkjh89a97f8',
            ...    consumer_key='jira-oauth-consumer',
            ...    access_token_secret='a9f8ag0ehaljkhgeds90',
            ...    key_cert='... some data here ...')._get_jira_parameters()
            Traceback (most recent call last):
              ...
            JIRASearcherException: Parameters given for both basic auth and OAuth
        """
        parameters = {
            'options': {
                'server': self.server
            }
        }

        if self.basic_auth_parameters and self.oauth_parameters:
            raise JIRASearcherException(
                'Parameters given for both basic auth and OAuth')
        elif self.oauth_parameters:
            parameters['oauth'] = self.oauth_parameters
        elif self.basic_auth_parameters:
            parameters['basic_auth'] = self.basic_auth_parameters

        return parameters

    def _get_basic_auth_parameters(self, username, password):
        """
        If enough parameters are given for basic authentication, returns
        a tuple suitable to jira.client.JIRA():

        >>> JIRASearcher()._get_basic_auth_parameters('foo', 'bar')
        ('foo', 'bar')

        If no parameter is given, returns None:

        >>> JIRASearcher()._get_basic_auth_parameters(None, None) is None
        True

        However, if one parameter is given and the other one is not, raises
        an exception:

        >>> JIRASearcher()._get_basic_auth_parameters('foo', None)
        Traceback (most recent call last):
          ...
        JIRASearcherException: Some, but not all, parameters passed to basic authentication
        """
        parameters = (username, password)

        if any(parameters) and not all(parameters):
            raise JIRASearcherException(
                'Some, but not all, parameters passed to basic authentication')

        return parameters if all(parameters) else None

    def _get_oauth_parameters(self, access_token, access_token_secret,
            consumer_key, key_cert):
        """
        If enough parameters are given for OAuth authentication, returns
        a dict suitable to jira.client.JIRA():

        >>> JIRASearcher()._get_oauth_parameters(
        ...    access_token='d87f3hajglkjh89a97f8',
        ...    consumer_key='jira-oauth-consumer',
        ...    access_token_secret='a9f8ag0ehaljkhgeds90',
        ...    key_cert='... some data here ...')
        {'access_token': 'd87f3hajglkjh89a97f8', 'consumer_key': 'jira-oauth-consumer', 'access_token_secret': 'a9f8ag0ehaljkhgeds90', 'key_cert': '... some data here ...'}

        If no parameter is given, returns None:

        >>> JIRASearcher()._get_oauth_parameters(None, None, None, None) is None
        True

        However, if one parameter is given and the other one is not, raises
        an exception:

        >>> JIRASearcher()._get_oauth_parameters(
        ...    access_token='d87f3hajglkjh89a97f8',
        ...    consumer_key=None,
        ...    access_token_secret='a9f8ag0ehaljkhgeds90',
        ...    key_cert='... some data here ...')
        Traceback (most recent call last):
          ...
        JIRASearcherException: Some, but not all, parameters passed to OAuth
        """
        parameters = {
            'access_token': access_token,
            'access_token_secret': access_token_secret,
            'consumer_key': consumer_key,
            'key_cert': key_cert
        }

        if any(parameters.values()) and not all(parameters.values()):
            raise JIRASearcherException(
                'Some, but not all, parameters passed to OAuth')

        return parameters if all(parameters.values()) else None

import argparse

def get_arg_parser():
    parser = argparse.ArgumentParser(
        description='Looks for LPS ticket flags in git history')

    parser.add_argument('-r', '--repository', dest='repository', default='.',
        help='Path to Git repository')
    parser.add_argument('-b', '--branch', dest='branch', default=None,
        help='Branch to be searched')

    parser.add_argument('-s', '--server', dest='server',
        default=LIFERAY_JIRA_SERVER, help='JIRA Server URL')
    parser.add_argument('-u', '--username', dest='username',
        help='JIRA user name')
    parser.add_argument('-p', '--password', dest='password',
        help='JIRA Password')
    parser.add_argument('issues', nargs='+', metavar='LPE-n',
        help='LPE issues whose related LPS issues should be found')

    return parser

if __name__ == '__main__':
    parser = get_arg_parser()

    arguments = parser.parse_args()

    gs = GitSearcher(arguments.repository, arguments.branch)
    js = JIRASearcher(server=arguments.server, username=arguments.username,
        password=arguments.password)
    issues = arguments.issues

    js.connect()
    related_issues = js.get_related_issues_set(issues)
    js.close()

    commits = gs.get_commits(related_issues)
    all_logs = ''.join(commits)

    not_found_issues = [issue
            for issue in related_issues
            if issue not in all_logs]

    for nfi in not_found_issues:
        print nfi
