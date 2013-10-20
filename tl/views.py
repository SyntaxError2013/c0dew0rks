from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib import messages
from django.utils.html import escape
from django.conf import settings
from django.utils.encoding import iri_to_uri
from django.utils.encoding import smart_str
from django.utils.http import urlquote
from django.views.decorators.csrf import csrf_exempt

from tl.models import *
from settings import MEDIA_ROOT
from settings import MEDIA_URL
from settings import STATIC_ROOT

from HTMLParser import HTMLParser

import pysrt
import urllib
import urllib2
import json
import os

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def to_milliseconds(t):
    return t.hours * (3600 * 1000) + t.minutes * (60 * 1000) + \
        t.seconds * 1000 + t.milliseconds

def removeNonAscii(s):
    return "".join(filter(lambda x: ord(x)<128, s))

def do_translate(s):
    """
    gc = gspread.login('annathirula@gmail.com', 'thisisthirula')
    sht = gc.open_by_key('0AuMhknOh8IOvdE9MQnpfQkZqOW9fLWF1QWRVVHhSZHc').sheet1
    """
    from_lang = detect_lang(s)
    to_lang = "en"

    # s = s.replace(' |', '').lower()
    API_KEY = 'trnsl.1.1.20131020T035719Z.8b9e2dcdc623229d.947805243b89b8ebd7310f344aa333d805ce4ff7'
    dic = {'key': API_KEY, 'lang': from_lang + '-' + to_lang, 'text': smart_str(s)}
    HTTP = "https://translate.yandex.net/api/v1.5/tr.json/translate?"

    #dic = {'text': smart_str(s), 'from': from_lang, 'to': to_lang, 'contentType': 'text/plain', 'Authorization': '1appsCY1Obo35s8X0gwua0yw3dR76eAQ4VxTzHZLhDs'}
    #HTTP = "https://api.datamarket.azure.com/Bing/MicrosoftTranslator/v1/Translate?"

    url_req = HTTP + urllib.urlencode(dic)
    r = urllib2.urlopen(url_req)
    r = r.read()
    json_list = json.loads(r)

    val = json_list['text'][0]
    """
    sht.update_acell('B2', '=gTranslate("' + s + '", "' + from_lang + '", "en")')
    val = sht.acell('B2').value
    """
    return val.split('|')

def detect_lang(s):
    API_KEY = '63dabb8028fbbf7b4d6203760e7ec553'
    dic = {'q': smart_str(s), 'key': API_KEY }
    url_req = 'http://ws.detectlanguage.com/0.2/detect?' + urllib.urlencode(dic)
    r = urllib2.urlopen(url_req)
    r = r.read()

    json_list = json.loads(r)
    lang = ''
    rating = 0

    for j in json_list['data']['detections']:
        if j['confidence'] >= rating:
            rating = j['confidence']
            lang = str(j['language'])

    return lang

########## Django views ###########

def index(request):
    """
    gc = gspread.login('annathirula@gmail.com', 'thisisthirula')
    sht1 = gc.open_by_key('0Ai0oPh0taW3FdDZFTmlWN2poSGY1U280LVpoUk1yaWc').sheet1
    sht1.update_acell('B2', '=gTranslate("this is a test", "en", "es")')
    """
    return render_to_response('tl/layout.html', {}, RequestContext(request))

@csrf_exempt
def translate(request):
    # First get the srt data
    import pdb;pdb.set_trace()
    ret_dict = {}
    if request.method == 'POST':
        final_str = ''
        # f = request.FILES['subs_file']
        fs = unicode(request.POST.items()[0][1])
        subs = pysrt.from_string(fs)

        # Get the translated version
        st_to_tl = ''
        for sub in subs:
            st_to_tl += sub.text + ' | '

        st_to_tl = strip_tags(st_to_tl[:-3])
        st_list = do_translate(st_to_tl)

        for i, sub in enumerate(subs):
            try:
                next_start = subs[i+1].start
            except Exception as e:
                print e
                final_str +=' ' + st_list[i] + '.'
                break
            break_duration = next_start - sub.end
            break_duration = to_milliseconds(break_duration)
            final_str += st_list[i] + '<break time="' + unicode(break_duration) + 'ms"/>'
        ret_dict['success'] = '1'
        ret_dict['api_key'] = '59e482ac28dd52db23a22aff4ac1d31e'
        ssml = '<?xml version="1.0"?> ' + \
         '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" ' + \
         'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' + \
         'xsi:schemaLocation="http://www.w3.org/2001/10/synthesis ' + \
            'http://www.w3.org/TR/speech-synthesis/synthesis.xsd" ' + \
         'xml:lang="en-US">' + final_str + '</speak>'
        import pdb;pdb.set_trace()
        ssml = smart_str(ssml)
        ret_dict['ssml'] = ssml
        json_response = json.dumps(ret_dict)
    else:
        json_response = '{"Hello" : "world"}'

    return HttpResponse(json_response, content_type="application/json")
