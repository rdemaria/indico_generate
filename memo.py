#!/usr/bin/env python3

import os
import sys
import time
import datetime

import simplejson
import requests
import jinja2


def serve(port=8123):
    import http.server
    import socketserver
    import threading

    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), Handler)
    print("serving at http://localhost:%s/"%port)
    thread = threading.Thread(target = httpd.serve_forever)
    thread.start()
    return httpd


def mydate(dt):
    return datetime.datetime.strptime(dt, '%Y-%m-%d').strftime('%A, %d %B %Y')

def get_category(categid):
    jsonfile = 'categ_%s.json' % categid
    if os.path.isfile(jsonfile):
        return simplejson.load(open(jsonfile))
    else:
        url = "https://indico.cern.ch/export/categ/%s.json" % (categid)
        resp = requests.get(url)
        open(jsonfile, 'w').write(resp.text)
        return resp.json()


def get_event(categid, eventid):
    dn = 'categ_%s' % categid
    if not os.path.isdir(dn):
        os.mkdir(dn)
    jsonfile = '%s/event_%s.json' % (dn, eventid)
    if os.path.isfile(jsonfile):
        return simplejson.load(open(jsonfile))
    else:
        url = "https://indico.cern.ch/export/event/%s.json" % (eventid)
        data = {'detail': 'contributions'}
        resp = requests.get(url, data)
        open(jsonfile, 'w').write(resp.text)
        return resp.json()


def export_txt(categid):
    catdata = get_category(categid)
    for event in catdata['results']:
        fmt = '{startDate[date]}: {title} {url}'
        print(fmt.format(**event))
        evdata = get_event(categid, event['id'])
        for contrib in evdata['results'][0]['contributions']:
            speakers = ['%s. %s' % (sp['first_name'][0], sp['last_name'])
                        for sp in contrib['speakers']]
            fmt = '  {title} (%s)' % (', '.join(speakers))
            print(fmt.format(**contrib))


def export_html(categid):
    out = []
    catdata = get_category(categid)
    for event in catdata['results']:
        fmt = '{startDate[date]}: {title} {url}'
        print(fmt.format(**event))
        evdata = get_event(categid, event['id'])
        for contrib in evdata['results'][0]['contributions']:
            speakers = ['%s. %s' % (sp['first_name'][0], sp['last_name'])
                        for sp in contrib['speakers']]
            fmt = '  {title} (%s)' % (', '.join(speakers))
            print(fmt.format(**contrib))


class Category(object):
    @classmethod
    def from_id(cls, categid):
        return cls(get_category(categid))

    def __init__(self, json):
        self.json = json
        self.id = json['additionalInfo']['eventCategories'][0]['categoryId']
        self.path = json['additionalInfo']['eventCategories'][0]['path']
        self.events = [Event.from_id(self.id, ev['id'])
                       for ev in json['results']]


class Event(object):
    @classmethod
    def from_id(cls, categid, eventid):
        return cls(get_event(categid, eventid))

    def __init__(self, json):
        self.json = json
        self.data = json['results'][0]
        self.__dict__.update(self.data)
        self.contributions = [Contribution(cn) for cn in self.contributions]
        if len(self.folders)>0:
            self.attachments=[ Attachment(at) for at in self.folders[0]['attachments'] ]
        self.date=mydate(self.startDate['date'])


class Contribution(object):
    def __init__(self, json):
        self.json = json
        self.__dict__.update(self.json)
        self.speakers = [Speaker(sp) for sp in self.speakers]
        if len(self.folders)>0:
            self.attachments=[ Attachment(at) for at in self.folders[0]['attachments'] ]

class Speaker(object):
    def __init__(self, json):
        self.json = json
        self.__dict__.update(self.json)

class Attachment(object):
    def __init__(self, json):
        self.json = json
        self.__dict__.update(self.json)
        if self.type=='file':
           self.short=self.download_url.split('.')[-1]
        elif self.type=='link':
           self.short=self.type
        else:
           self.short=self.json

# export_txt(sys.argv[1])

def export(categ,tmpfile):
   ftype=tmpfile.split('.')[0]
   outfile='%s.%s'%(categ.id,ftype)
   template = jinja2.Template(open(tmpfile).read())
   out=template.render(categ=categ)
   open(outfile,'w').write(out)
   print(outfile)


categid=sys.argv[1]
tmpfile=sys.argv[2]
categ = Category.from_id(categid)
export(categ,tmpfile)

