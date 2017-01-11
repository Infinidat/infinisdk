#!/usr/bin/env python
from __future__ import print_function
import datetime
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
def main(verbose, quiet):
    with logbook.NullHandler(), logbook.StreamHandler(sys.stderr, level=logbook.WARNING - verbose + quiet, bubble=False):
        repo = Checkout()
        repo.clone()
        repo.start_release()
        repo.fetch_ours()
        repo.reshape()
        repo.generate_changelog()
        repo.commit()
        repo.tag()
        input('Committed and tagged under {} [Press Enter to continue]'.format(repo.path))


class Checkout(object):

    def __init__(self):
        super(Checkout, self).__init__()
        self.path = os.path.join(tempfile.mkdtemp(), 'repo')

    def clone(self):
        email = subprocess.check_output('git config user.email', shell=True, cwd='.').decode('utf-8').strip()
        self._execute('git clone https://github.com/Infinidat/infinisdk {}'.format(self.path), cwd='.')
        self._execute('git config user.email {}'.format(email), cwd=self.path)
        self._execute('git flow init -d', cwd=self.path)
        _logger.info('Checked out to {}', self.path)

    def start_release(self):
        last_released = self._get_released_version()
        new_version = last_released + '.post1'
        self._execute('git flow release start {}.post1'.format(last_released), cwd=self.path)
        version_file = os.path.join(self.path, 'infinisdk', '__version__.py')

        if not os.path.isfile(version_file):
            raise RuntimeError('Version file {} does not exist'.format(version_file))

        with open(os.path.join(self.path, 'infinisdk', '__version__.py'), 'w') as f:
            print('__version__ =', repr(new_version), file=f)


    def fetch_ours(self):
        self._execute('git fetch {}'.format(os.path.abspath('.')))
        self._execute('git checkout FETCH_HEAD -- .')

    def reshape(self):
        shutil.rmtree(os.path.join(self.path, 'tests'))
        shutil.rmtree(os.path.join(self.path, 'scripts'))

    def generate_changelog(self):
        version = self._get_released_version()
        changelog_filename = os.path.join(self.path, 'CHANGELOG')
        new_changelog_filename = changelog_filename + '.new'

        last_released = self._get_last_released_tag()

        _logger.debug('Last released version: {}', last_released)

        with open(new_changelog_filename, 'w') as changelog:
            title = 'Version {} (Released {:%Y-%m-%d})'.format(version, datetime.datetime.now())
            print('{}\n{}\n'.format(title, '-' * len(title)), file=changelog)

            for issue in jira_client.search('project = "INFRADEV" and '
                                            'component = "InfiniSDK" and '
                                            'resolution is not empty and '
                                            'fixVersion is not empty and '
                                            '"Release Notes Title" is not empty'):
                if last_released is None or int(issue.fixVersion) > last_released:
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
                sorted_tags.append(int(tag))
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
        self._execute('git commit -m "v{}"'.format(self._get_released_version()))

    def tag(self):
        self._execute('git tag {}'.format(self._get_released_version()))

    def _execute(self, cmd, cwd=None):
        if cwd is None:
            cwd = self.path
        _logger.debug('Running {}', cmd)
        subprocess.check_call(cmd, shell=True, cwd=cwd)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
