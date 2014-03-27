#!/usr/bin/env python

import git

def get_ticket_flags(tickets, branch=None):
    """
    Generate the expected flags for 'git log'

    Usage:

    >>> get_ticket_flags(['LPS-1', 'LPS-2'])
    ['--grep=LPS-1', '--grep=LPS-2']
    >>> get_ticket_flags(['LPS-1', 'LPS-2'], '6.2.x')
    ['--grep=LPS-1', '--grep=LPS-2', '6.2.x']
    """
    flags = ['--grep={}'.format(ticket) for ticket in tickets]

    if branch:
        flags.append(branch)

    return flags

def get_commits(repository, branch, tickets):
    """
    Find all commits with the listed tickets.

    Usage:

    >>> get_commits(git.Git('.'), 'master', ['LPS-32', 'LPS-33'])
    ['4748d69 LPS-33 Removing example', '5fa1862 LPS-32 Just an example']
    """
    flags = get_ticket_flags(tickets, branch)

    commits = repository.log(['--oneline'] + flags).split('\n')

    return commits

def print_commits(commits):
    """
    Print the found commits
    """
    for commit in commits:
        print(commit)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Looks for LPS ticket flags in git history')

    parser.add_argument('-r', '--repository', dest='repository', default='.',
        help='Path to Git repository')
    parser.add_argument('-b', '--branch', dest='branch', default=None,
        help='Branch to be searched')
    parser.add_argument('tickets', nargs='+', metavar='LPS-n',
        help='Tickets to be found')

    arguments = parser.parse_args()

    repository = git.Git(arguments.repository)
    branch = arguments.branch
    tickets = arguments .tickets

    commits = get_commits(repository, branch, tickets)

    print_commits(commits)
