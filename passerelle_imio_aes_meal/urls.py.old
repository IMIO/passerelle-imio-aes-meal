from django.conf.urls import patterns, include, url
from .views import (DatasourcesView,
		    MotivationtermAddView,
		    MotivationtermDeleteView,
		    MotivationtermUpdateView,
		    DestinationtermAddView,
		    DestinationtermDeleteView,
		    DestinationtermUpdateView)


urlpatterns = patterns('',
    url(r'^(?P<slug>[\w,-]+)/data$', DatasourcesView.as_view(), name='DatasourcesView-data'),
)

management_urlpatterns = patterns('',
    url(r'^(?P<connector_slug>[\w,-]+)/motivationterm/add/',
	MotivationtermAddView.as_view(), name='motivationterm-add'),
    url(r'^(?P<connector_slug>[\w,-]+)/motivationterm/(?P<pk>[\w,-]+)/delete/',
	MotivationtermDeleteView.as_view(), name='motivationterm-delete'),
    url(r'^(?P<connector_slug>[\w,-]+)/motivationterm/(?P<pk>[\w,-]+)/update/',
	MotivationtermUpdateView.as_view(), name='motivationterm-update'),
    url(r'^(?P<connector_slug>[\w,-]+)/destinationterm/add/',
	DestinationtermAddView.as_view(), name='destinationterm-add'),
    url(r'^(?P<connector_slug>[\w,-]+)/destinationterm/(?P<pk>[\w,-]+)/delete/',
	DestinationtermDeleteView.as_view(), name='destinationterm-delete'),
    url(r'^(?P<connector_slug>[\w,-]+)/destinationterm/(?P<pk>[\w,-]+)/update/',
	DestinationtermUpdateView.as_view(), name='destinationterm-update')	
)
