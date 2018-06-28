#!/usr/bin/env python
from __future__ import print_function
import datetime
import itertools
import os
import shutil
import subprocess
import sys
import tempfile

import logbook
import click
from ecosystem.jira import client as jira_client

_logger = logbook.Logger(__name__)


@click.command()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet", count=True)
@click.option("--path", default=None)
@click.option("--version", required=True)
def main(verbose, quiet, version, path):
    with logbook.NullHandler(), logbook.StreamHandler(sys.stderr, level=logbook.WARNING - verbose + quiet, bubble=False):
        repo = Checkout(version=version, path=path)
        repo.clone()
        repo.start_release()
        repo.fetch_ours()
        repo.reshape()
        repo.generate_changelog()
        repo.commit()
        input('Committed and tagged under {} [Press Enter to continue]'.format(repo.path))


class Checkout(object):

    def __init__(self, version, path=None):
        super(Checkout, self).__init__()
        if path is None:
            path = os.path.join(tempfile.mkdtemp(), 'repo')
        self.path = path
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        self._version = version

    def clone(self):
        email = subprocess.check_output('git config user.email', shell=True, cwd='.').decode('utf-8').strip()
        self._execute('git clone git@github.com:Infinidat/infinisdk {}'.format(self.path), cwd='.')
        self._execute('git config user.email {}'.format(email))
        self._execute('git flow init -d')
        _logger.info('Checked out to {}', self.path)

    def start_release(self):
        self._execute('git flow release start {}'.format(self._version), cwd=self.path)


    def fetch_ours(self):
        self._execute('git fetch {}'.format(os.path.abspath('.')))
        self._execute('git reset --hard FETCH_HEAD')
        self._execute('git reset master')
        self._execute('git checkout -- CHANGELOG')
        self._execute('git add .')
        version_file = os.path.join(self.path, 'infinisdk', '__version__.py')

        if not os.path.isfile(version_file):
            raise RuntimeError('Version file {} does not exist'.format(version_file))

        with open(os.path.join(self.path, 'infinisdk', '__version__.py'), 'w') as f:
            print('__version__ =', repr(self._version), file=f)


    def reshape(self):
        shutil.rmtree(os.path.join(self.path, 'tests'))
        shutil.rmtree(os.path.join(self.path, 'scripts'))

    def generate_changelog(self):
        changelog_filename = os.path.join(self.path, 'CHANGELOG')
        new_changelog_filename = changelog_filename + '.new'

        last_released = self._get_last_released_tag()
        assert last_released is not None

        _logger.debug('Last released version: {}', last_released)

        with open(new_changelog_filename, 'w') as changelog:
            title = 'Version {} (Released {:%Y-%m-%d})'.format(self._version, datetime.datetime.now())
            print('{}\n{}\n'.format(title, '-' * len(title)), file=changelog)

            for issue in jira_client.search('project = "INFRADEV" and '
                                            'component = "InfiniSDK" and '
                                            'resolution is not empty and '
                                            'fixVersion is not empty and '
                                            '"Release Notes Title" is not empty'):

                if any(_normalize_version(self._version) > _normalize_version(fix_version) > _normalize_version(last_released) # pylint: disable=line-too-long
                       for fix_version in issue.get_fix_versions()):

                    print('*', '#{}'.format(issue.key.split('-')
                                            [1]), issue._data.fields.customfield_12507, file=changelog)  # pylint: disable=protected-access

            print(file=changelog)

            if os.path.exists(changelog_filename):
                with open(changelog_filename) as old_changelog:
                    for line in old_changelog:
                        changelog.write(line)

        os.rename(new_changelog_filename, changelog_filename)
        _logger.info('New changelog written to {}', changelog_filename)

    def _get_last_released_tag(self):
        tags = subprocess.check_output('git tag', cwd=self.path, shell=True).decode('utf-8').splitlines()
        sorted_tags = []
        for tag in tags:
            try:
                sorted_tags.append(_normalize_version(tag))
            except ValueError:
                continue
            sorted_tags.append(tag)
        sorted_tags.sort(reverse=True)
        return sorted_tags[0] if sorted_tags else None

    def _get_released_version(self):
        output = subprocess.check_output('git describe --tags', shell=True).decode('utf-8').strip().split('-')[0]
        return output

    def commit(self):
        self._execute('git add .')
        self._execute('git commit -m "v{}"'.format(self._version))

    def _execute(self, cmd, cwd=None):
        if cwd is None:
            cwd = self.path
        _logger.debug('Running {}', cmd)
        subprocess.check_call(cmd, shell=True, cwd=cwd)


def _normalize_version(version):
    version = str(version)
    if not version.split('.')[0].isdigit():
        raise ValueError('Invalid version specified: {!r}'.format(version))
    while version.count('.') < 2:
        version += '.0'
    return version

if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
