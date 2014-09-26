from django.conf.urls import patterns, include, url
from django.contrib import admin

from age_atlas import views

urlpatterns = patterns('',
        url(r'^$', views.index,
            name='index'),
        url(r'^tutorial/', views.tutorial,
            name='tutorial'),
        url(r'^statistics/', views.statistics,
            name='statistics'),
        url(r'^query/tissue/', views.query_tissue,
            name='query_tissue'),

        url(r'^autocomplete/', include([
            url('tissue$', views.autocomplete_tissue),
            url('species$', views.autocomplete_species)
        ]))
)
