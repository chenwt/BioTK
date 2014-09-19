from django.conf.urls import patterns, url

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
)
