#!/usr/bin/env python
'''
replace strings on pages
'''

import datetime, xmlrpclib, sys, tempfile

from optparse import OptionParser
parser = OptionParser("replace_all.py [options] <search> <replace>")
parser.add_option("--username", help="Wordpress username", default=None)
parser.add_option("--password", help="Wordpress password", default=None)
parser.add_option("--url", help="Source Wordpress URL", default=None)
parser.add_option("--title-prefix", help="title prefix to look for", default="common-")
parser.add_option("--blog-id", help="ID of wiki", default='')

(opts, args) = parser.parse_args()

if len(args) < 2:
    print("You must supply a search and replace string")
    sys.exit(1)

if opts.url is None:
    print("You must supply a base URL")
    sys.exit(1)

search_str = args[0]
replace_str = args[1]

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
    changed = False
    if post['post_content'].find(search_str) != -1:
        post['post_content'] = post['post_content'].replace(search_str, replace_str)
        changed = True
    if changed:
        new_post = { 'post_content' : post['post_content'] }
        print("Uploading")
        if not src_server.wp.editPost(opts.blog_id, opts.username, opts.password, posts[title], new_post):
            print("Failed to update %s" % title)
            exit_code = 1
    else:
        print("No change")

sys.exit(exit_code)
