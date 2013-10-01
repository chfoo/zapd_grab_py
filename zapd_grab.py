#!/usr/bin/python
# encoding=utf-8
'''Grabs zapd'''
from PySide.QtNetwork import QNetworkProxy
import argparse
import atexit
import ghost
import logging
import os
import subprocess
import time
import lxml.etree

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


class Scraper(object):
    def __init__(self, hostname, proxy_port, out_path=None):
        super(Scraper, self).__init__()
        self._hostname = hostname
        self._proxy_port = proxy_port
        self._out_path = out_path

        self._init_proxy()

        self._ghost = ghost.Ghost(ignore_ssl_errors=True, wait_timeout=60)

    def _init_proxy(self):
        _logger.debug('Initialize proxy')
        proxy = QNetworkProxy(QNetworkProxy.HttpProxy, "localhost",
            self._proxy_port)
        QNetworkProxy.setApplicationProxy(proxy)

        self._proxy_proc = subprocess.Popen(['python', '-m',
            'tornado_proxy.proxy', str(self._proxy_port)])

        atexit.register(self._proxy_proc.terminate)

    def _get_sub_zapds(self, source):
        root = lxml.etree.HTML(source)

        for neighbor in root.iter('a'):
            href = neighbor.attrib.get('href')

            if href and self._hostname in href:
                yield href

    def run(self):
        _logger.info('Running..')

        stop_after_this_page = False

        # 1: Visit the user's Zapd page.
        page, resources = self._ghost.open('http://{}'.format(self._hostname))

        # 2: Expand the "see all" links for kicks.  Also, this gives us a
        # full list of followers and followees.
        _logger.debug('Click on see all')
        self._ghost.click('a.see-all')

        next_clicks = 0

        while True:
            # 3: For this page, click on each of the zapds.
            done = set()
            remaining = set(self._get_sub_zapds(self._ghost.content)) - done

            while True:
                if not remaining:
                    break
                l = remaining.pop()
                _logger.info('Visiting {}'.format(l))

                page, resources = self._ghost.open(l)

                # 4: Go back home.
                self._ghost.click('.page-header-creator-name a')

                self._ghost.wait_for_page_loaded()

                # Get back to the right place.
                for dummy in xrange(next_clicks):
                    self._ghost.click('a.next_page')
                    self._ghost.wait_for_page_loaded()

                done.add(l)
                remaining = set(self._get_sub_zapds(self._ghost.content)) - done

            if stop_after_this_page:
                break

            # 5: Repeat 3-4 for each additional page on the main Zapd page.
            if self._ghost.exists('a.next_page'):
                next_clicks += 1
                _logger.info('Going to page {}'.format(next_clicks + 1))

                for dummy in xrange(next_clicks):
                    self._ghost.click('a.next_page')
                    self._ghost.wait_for_page_loaded()
            else:
                _logger.info('No more pages; finishing up fetch')
                stop_after_this_page = True

        if self._out_path:
            os.rename('out.warc.gz', self._out_path)
        else:
            os.rename('out.warc.gz', '{}-{}.warc.gz'.format(
                int(time.time()),
                self._hostname
            ))

        _logger.info('Done')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _logger.debug('Debug logging on')
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('hostname')
    arg_parser.add_argument('--proxy-port', default=8192,
        help='Port number for proxy')
    arg_parser.add_argument('--output', help='Path of warc file to output')

    args = arg_parser.parse_args()

    scraper = Scraper(args.hostname, args.proxy_port, out_path=args.output)
    scraper.run()
