from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^age_atlas/', 
        include("age_atlas.urls", namespace="age_atlas")),
    url(r'^admin/', include(admin.site.urls)),
)
