# -*- coding: utf-8 -*-
"""Tumblr pictures crawler/downloader

This application receives a public Tumblr name and start downloading
the full resolution picture files until the last page. It can generate
big volumes of output data.

Example:

        $ python download_tubmlr.py some-tumblr-i-love

DISCLAIMER: This is not an official Tumblr application and maybe its use
is not even authorized by them. So use it by your own risk.

Furthermore, the application purpose is for those who still lives in a
decade ago and don't trust too much in the cloud, usually downloading
lots of data to **keep for themselves**. Please don't use this application
nor for copyright violation purposes, neither for unauthorized personal
image reproduction or reuse.

I just love some works exposed in Tumblr and want to keep them as a
personal collection. If you want the same, feel free to use and modify
this application.
"""


from bs4 import BeautifulSoup as BS
from urllib2 import urlopen
from urlparse import urlparse
from multiprocessing import Pool, get_logger
from functools import partial
import os.path as op
import os
import logging.handlers
import sys

console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s",
                                        "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(console_formatter)
get_logger().addHandler(console_handler)
get_logger().setLevel(logging.INFO)

TUMBLR_NAME = sys.argv[1]
BASE_URL = 'http://{}.tumblr.com'.format(TUMBLR_NAME)


def download_photoset(i, photoset_paths, page):
    try:
        len_posts = len(photoset_paths)
        post_path = photoset_paths[i]
        u = urlopen(BASE_URL + post_path)
        bs = BS(u, 'html.parser')
        post_imgs = [a.attrs['href'] for a in bs.find_all('a') if a.attrs['href']]
        len_imgs = len(post_imgs)
        for j in range(len_imgs):
            img_url = post_imgs[j]
            get_logger().info('PAGE %03d downloading image %02d/%02d from photoset %02d/%02d', page, j + 1, len_imgs, i + 1, len_posts)
            get_logger().debug('URL: %s', img_url)
            u = urlopen(img_url)
            with open(op.join('.', TUMBLR_NAME, str(page), urlparse(img_url).path.split('/')[-1]), 'wb') as f:
                f.write(u.read())
        return 0
    except KeyboardInterrupt:
        return 1


def download_photo(i, photo_paths, page):
    try:
        img_url = photo_paths[i]
        get_logger().info('PAGE %03d downloading photo %02d/%02d', page, i + 1, len(photo_paths))
        get_logger().debug('URL: %s', img_url)
        u = urlopen(img_url)
        with open(op.join('.', TUMBLR_NAME, str(page), urlparse(img_url).path.split('/')[-1]), 'wb') as f:
            f.write(u.read())
        return 0
    except KeyboardInterrupt:
        return 1


if not op.exists(op.join('.', TUMBLR_NAME)):
    os.mkdir(op.join('.', TUMBLR_NAME))

page = 1
len_posts = 1
p = Pool()

while len_posts > 0:
    u = urlopen('{}/page/{}'.format(BASE_URL, page))
    bs = BS(u, 'html.parser')

    # get the photosets iframes on the page
    photoset_paths = [
        i.attrs['src'] 
        for i in bs.find_all('iframe') 
        if i.attrs.get('src', '').startswith('/post')
           and i.attrs.get('src', '').find(TUMBLR_NAME) > -1  # avoids 'recently liked' references to other tumblrs
    ]
    len_photosets = len(photoset_paths)

    # get the single photo posts on the page
    photo_paths = [
        i.attrs['src']
        for i in bs.select('div.photo-wrapper-inner > a > img') + bs.select('div.photo-wrapper-inner > img')
    ]
    len_photos = len(photo_paths)

    # loop with multiprocesses to download the files in parallel
    len_posts = len_photosets + len_photos
    if len_posts > 0:
        page_dir = op.join('.', TUMBLR_NAME, str(page))
        if not op.exists(page_dir):
            os.mkdir(page_dir)
        get_logger().info('PAGE %03d starting download with %02d posts', page, len_posts)
        
        results = p.map(partial(download_photoset, photoset_paths=photoset_paths, page=page), range(len_photosets)) + \
                  p.map(partial(download_photo, photo_paths=photo_paths, page=page), range(len_photos))
        if any(results):
            p.terminate()
            break
        page = page + 1
