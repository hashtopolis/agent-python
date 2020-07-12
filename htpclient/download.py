import logging
from time import sleep

import requests
import sys
import os

from htpclient.initialize import Initialize
from htpclient.session import Session


class Download:
    @staticmethod
    def download(url, output, no_header=False):
        try:
            session = Session().s
            if Initialize.get_os() == 1:
                output = output.replace("/", '\\')

            # Check header
            if not no_header:
                head = session.head(url)
                # not sure if we only should allow 200/302, but then it's present for sure
                if head.status_code != 200 and head.status_code != 302:
                    logging.error("File download header reported wrong status code: " + str(head.status_code))
                    return False

            with open(output, "wb") as file:
                response = session.get(url, stream=True)
                total_length = response.headers.get('Content-Length')

                if total_length is None:  # no content length header
                    file.write(response.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        file.write(data)
                        done = int(50 * dl / total_length)
                        sys.stdout.write("\rDownloading: [%s%s]" % ('=' * done, ' ' * (50 - done)))
                        sys.stdout.flush()
            sys.stdout.write("\n")
            return True
        except requests.exceptions.ConnectionError as e:
            logging.error("Download error: " + str(e))
            sleep(30)
            return False

    @staticmethod
    def rsync(remote_path, local_path):
        logging.info('getting file "%s" via rsync' % local_path.split('/')[-1])
        os.system('rsync -avzP --partial %s %s' % (remote_path, local_path))
