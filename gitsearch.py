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

import jira.client

LIFERAY_JIRA_SERVER = 'http://issues.liferay.com'

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

    searcher = GitSearcher(arguments.repository, arguments.branch)

    commits = searcher.get_commits(arguments.tickets)

    for commit in commits:
        print(commit)
