import argparse
from deployd.common.config import Config
from deployd.common.status_code import Status
from deployd.download.download_helper_factory import DownloadHelperFactory
import os
import re
import sys
import tarfile
import zipfile
import logging
import traceback

log = logging.getLogger(__name__)


class Downloader(object):

    def __init__(self, config_fn, build, url, env_name):
        config = Config(config_fn)
        self._matcher = re.compile(r'^.*?[.](?P<ext>tar\.gz|tar\.bz2|\w+)$')
        self._base_dir = config.get_builds_directory()
        self._build_name = env_name
        self._build = build
        self._url = url

    def _get_extension(self, url):
        return self._matcher.match(url).group('ext')

    def download(self):
        extension = self._get_extension(self._url.lower())
        local_fn = u'{}-{}.{}'.format(self._build_name, self._build, extension)
        local_full_fn = os.path.join(self._base_dir, local_fn)
        extracted_file = os.path.join(self._base_dir, '{}.extracted'.format(self._build))
        if os.path.exists(extracted_file):
            log.info("{} exists. tarball have already been extracted.".format(extracted_file))
            return Status.SUCCEEDED

        working_dir = os.path.join(self._base_dir, self._build)
        if not os.path.exists(working_dir):
            log.info('Create directory {}.'.format(working_dir))
            os.mkdir(working_dir)

        downloader = DownloadHelperFactory.gen_downloader(self._url)
        if downloader:
            status = downloader.download(local_full_fn)
            if status != Status.SUCCEEDED:
                return status
        else:
            return Status.FAILED

        curr_working_dir = os.getcwd()
        os.chdir(working_dir)
        try:
            if extension == 'zip':
                log.info("unzip files to {}".format(working_dir))
                with zipfile.ZipFile(local_full_fn) as zfile:
                    zfile.extractall(working_dir)
            else:
                log.info("untar files to {}".format(working_dir))
                with tarfile.open(local_full_fn) as tfile:
                    tfile.extractall(working_dir)

            # change the working directory back
            os.chdir(curr_working_dir)
            with file(extracted_file, 'w'):
                pass
            log.info("Successfully extracted {} to {}".format(local_full_fn, working_dir))
        except tarfile.TarError as e:
            status = Status.FAILED
            log.error("Failed to extract files: {}".format(e.message))
        except OSError as e:
            status = Status.FAILED
            log.error("Failed: {}".format(e.message))
        except Exception:
            status = Status.FAILED
            log.error(traceback.format_exc())
        finally:
            return status


def main():

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-f', '--config-file', dest='config_file', default=None,
                        help="the deploy agent conf file filename path. If none, "
                             "/etc/deployagent.conf will be used")
    parser.add_argument('-v', '--build-version', dest='build', required=True,
                        help="the current deploying build version for the current environment.")
    parser.add_argument('-u', '--url', dest='url', required=True,
                        help="the url of the source code where the downloader would download from. "
                             "The url can start"
                             "with s3:// or https://")
    parser.add_argument('-e', '--env-name', dest='env_name', required=True,
                        help="the environment name currently in deploy.")
    args = parser.parse_args()

    status = Downloader(args.config_file, args.build, args.url, args.env_name).download()
    if status != Status.SUCCEEDED:
        log.error("Download failed.")
        sys.exit(1)
    else:
        log.info("Download succeeded.")
        sys.exit(0)

if __name__ == '__main__':
    main()
