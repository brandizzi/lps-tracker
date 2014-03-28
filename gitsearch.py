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

import argparse

def get_arg_parser():
    parser = argparse.ArgumentParser(
        description='Looks for LPS ticket flags in git history')

    parser.add_argument('-r', '--repository', dest='repository', default='.',
        help='Path to Git repository')
    parser.add_argument('-b', '--branch', dest='branch', default=None,
        help='Branch to be searched')
    parser.add_argument('tickets', nargs='+', metavar='LPS-n',
        help='Tickets to be found')

    return parser

if __name__ == '__main__':
    parser = get_arg_parser()

    arguments = parser.parse_args()

    searcher = GitSearcher(arguments.repository, arguments.branch)

    commits = searcher.get_commits(arguments.tickets)

    for commit in commits:
        print(commit)
