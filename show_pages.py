#!/usr/bin/env python
'''
show details of a page
'''

import datetime, xmlrpclib, sys, tempfile

from optparse import OptionParser
parser = OptionParser("show_pages.py [options]")
parser.add_option("--username", help="Wordpress username", default=None)
parser.add_option("--password", help="Wordpress password", default=None)
parser.add_option("--url", help="Source Wordpress URL", default=None)
parser.add_option("--title-prefix", help="title prefix to look for", default="common-")
parser.add_option("--blog-id", help="ID of wiki", default='')

(opts, args) = parser.parse_args()

if opts.url is None:
    print("You must supply a base URL")
    sys.exit(1)

src_server = xmlrpclib.ServerProxy(opts.url + '/xmlrpc.php')

def find_post_by_title_prefix(server, title_prefix):
    '''find the source posts'''
    posts = server.wp.getPosts(opts.blog_id, opts.username, opts.password,
                               { 'post_type' : 'wiki', 'number' : 1000000 },
                               [ 'post_title', 'post_id' ])
    ret = {}
    for p in posts:
        if p['post_title'].startswith(title_prefix):
            ret[p['post_title']] = p['post_id']
    return ret

posts = find_post_by_title_prefix(src_server, opts.title_prefix)
if not posts:
    print("No matching posts found")
    sys.exit(1)

exit_code = 0

for title in posts.keys():
    print("Fetching %s" % title)
    post = src_server.wp.getPost(opts.blog_id, opts.username, opts.password, posts[title])
    print post

sys.exit(exit_code)
