#!/usr/bin/env python
'''
copy common-* pages from one site to another
'''

import datetime, xmlrpclib, sys, tempfile

from optparse import OptionParser
parser = OptionParser("copy_common.py [options]")
parser.add_option("--username", help="Wordpress username", default=None)
parser.add_option("--password", help="Wordpress password", default=None)
parser.add_option("--url-src", help="Source Wordpress URL", default=None)
parser.add_option("--url-dst", help="Destination Wordpress URL", default=None)
parser.add_option("--title-prefix", help="title prefix to look for", default="common-")
parser.add_option("--blog-id", help="ID of wiki", default='')

(opts, args) = parser.parse_args()

if opts.url_src is None or opts.url_dst is None:
    print("You must supply a base URL for both wordpress sites")
    sys.exit(1)

if opts.username is None or opts.password is None:
    print("You must supply a username and password")
    sys.exit(1)

src_server = xmlrpclib.ServerProxy(opts.url_src + '/xmlrpc.php')
dst_server = xmlrpclib.ServerProxy(opts.url_dst + '/xmlrpc.php')

def find_post_by_title_prefix(server, title_prefix):
    '''find the source posts'''
    posts = server.wp.getPosts(opts.blog_id, opts.username, opts.password,
                               { 'post_type' : 'wiki', 'number' : 1000000 },
                               [ 'post_title', 'post_id', 'post_modified' ])
    ret = {}
    for p in posts:
        if p['post_title'].startswith(title_prefix):
            ret[p['post_title']] = { 'post_id' : p['post_id'], 'post_modified' : p['post_modified'] }
    return ret

posts = find_post_by_title_prefix(src_server, opts.title_prefix)
if not posts:
    print("No matching posts found")
    sys.exit(1)

dst_posts = find_post_by_title_prefix(dst_server, opts.title_prefix)

exit_code = 0

# which fields to copy over

new_keys = ['post_mime_type', 'post_date_gmt', 'sticky', 'post_date',
            'post_type', 'post_modified', 'custom_fields',
            'post_title', 'post_status', 'post_content',
            'terms', 'post_thumbnail', 'ping_status',
            'comment_status', 'post_format', 'post_name',
            'post_modified_gmt', 'post_excerpt']


for title in posts.keys():
    if title in dst_posts and posts[title]['post_modified'] <= dst_posts[title]['post_modified']:
        #print("Destination is newer for %s" % title)
        continue

    print("Fetching %s" % title)
    post = src_server.wp.getPost(opts.blog_id, opts.username, opts.password, posts[title]['post_id'])

    new_post = {}
    for k in new_keys:
        new_post[k] = post[k]

    # force author to be autotest
    new_post['post_author'] = 'autotest'
    new_post['post_content'] = new_post['post_content'].replace('[common_page]', '')
    new_post['post_content'] = new_post['post_content'].replace('[common_page_mp]', '')
    print("Adding common_page")
    if opts.url_src.find('planner') != -1:
        new_post['post_content'] = '[common_page_mp]\n\n' + new_post['post_content']
    else:
        new_post['post_content'] = '[common_page]\n\n' + new_post['post_content']

    if title in dst_posts:
        dst_post = dst_server.wp.getPost(opts.blog_id, opts.username, opts.password, dst_posts[title]['post_id'])

        if post['post_modified'] <= dst_post['post_modified']:
            print("Destination is newer")
            continue

        print("Uploading %s" % title)
        if not dst_server.wp.editPost(opts.blog_id, opts.username, opts.password, dst_posts[title]['post_id'], new_post):
            print("Failed to update %s" % title)
            exit_code = 1
    else:
        print("Uploading %s" % title)

        if not dst_server.wp.newPost(opts.blog_id, opts.username, opts.password, new_post):
            print("Failed to upload %s" % title)
            exit_code = 1

sys.exit(exit_code)
