from django.conf.urls.defaults import *
from tl.views import *

urlpatterns = patterns('',
                       # Hello,
                       url(r'^$', index),
                       url(r'^translate/$', translate),
                   )
