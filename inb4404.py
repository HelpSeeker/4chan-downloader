#!/usr/bin/python3

import argparse
import logging
import os
import re
import time

import urllib.error
from urllib.request import urlopen

log = logging.getLogger('inb4404')
workpath = os.path.dirname(os.path.realpath(__file__))
args = None


def parse_cli():
    global args

    parser = argparse.ArgumentParser(description='inb4404')
    parser.add_argument(
        'thread', nargs=1,
        help='url of the thread (or filename; one url per line)')
    parser.add_argument(
        '-c', '--with-counter', action='store_true',
        help='show a counter next the the image that has been downloaded')
    parser.add_argument(
        '-d', '--date', action='store_true',
        help='show date as well')
    parser.add_argument(
        '-l', '--less', action='store_true',
        help='show less information (surpresses checking messages)')
    parser.add_argument(
        '-n', '--use-names', action='store_true',
        help='use thread names instead of the thread ids')
    parser.add_argument(
        '-r', '--reload', action='store_true',
        help='reload the queue file every 5 minutes')

    args = parser.parse_args()


def load(url):
    with urlopen(url) as resp:
        return resp.read()


def download_thread(thread_link):
    board = thread_link.split('/')[3]
    thread = thread_link.split('/')[5].split('#')[0]
    if len(thread_link.split('/')) > 6:
        thread_tmp = thread_link.split('/')[6].split('#')[0]

        if args.use_names or os.path.exists(os.path.join(workpath, 'downloads', board, thread_tmp)):
            thread = thread_tmp

    directory = os.path.join(workpath, 'downloads', board, thread)
    if not os.path.exists(directory):
        os.makedirs(directory)

    while True:
        try:
            regex = '(\/\/i(?:s|)\d*\.(?:4cdn|4chan)\.org\/\w+\/(\d+\.(?:jpg|png|gif|webm)))'
            regex_result = list(set(re.findall(regex, load(thread_link).decode('utf-8'))))
            regex_result = sorted(regex_result, key=lambda tup: tup[1])
            regex_result_len = len(regex_result)
            regex_result_cnt = 1

            for link, img in regex_result:
                img_path = os.path.join(directory, img)
                if not os.path.exists(img_path):
                    data = load('https:' + link)

                    output_text = board + '/' + thread + '/' + img
                    if args.with_counter:
                        output_text = '[' + str(regex_result_cnt).rjust(len(str(regex_result_len))) +  '/' + str(regex_result_len) + '] ' + output_text

                    log.info(output_text)

                    with open(img_path, 'wb') as f:
                        f.write(data)

                regex_result_cnt += 1

        except urllib.error.HTTPError:
            time.sleep(10)
            try:
                load(thread_link)
            except urllib.error.HTTPError:
                log.info('%s 404\'d', thread_link)
                break
            continue
        except urllib.error.URLError:
            if not args.less:
                log.warning('Something went wrong')

        if not args.less:
            log.info('Checking ' + board + '/' + thread)
        time.sleep(20)


def main():
    parse_cli()

    if args.date:
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%I:%M:%S %p')

    thread = args.thread[0].strip()
    download_thread(thread)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
