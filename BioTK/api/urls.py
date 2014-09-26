from django.conf.urls import patterns, url, include

from BioTK.api import views

urlpatterns = patterns(
    '',

    url(r'^$', views.index, name="index"),

    url(r'^tissue/list', views.tissue_list),

    url(r'^(?P<taxon_id>[0-9]+)/', include([
        url(r'^tissue/', include([
            url(r'^(?P<tissue>BTO:[0-9]+)/', include([
                url('^correlation/age', views.tissue_age_correlation)
            ]))
        ])),

        url(r'^matrix/(?P<type>(raw|normalized))/',
            include([
                url(r'^gene/',
                    include([
                        url(r'^(?P<gene_id>[A-Za-z0-9]+)/$',
                            views.matrix_gene),
                        url(r'^list', views.matrix_list, {"index": "gene"})
                    ])),
                url(r'^sample/',
                    include([
                        url(r'(?P<sample_accession>[A-Za-z0-9]+-[0-9]+)$',
                            views.matrix_sample),
                        url(r'^list', views.matrix_list, {"index": "sample"})
                    ]))
            ])),
        url(r'gene/(?P<gene_id>[0-9]+)/',
            include([
                url(r'correlation/age/(?P<tissue>BTO:[0-9]+)/$',
                    views.not_implemented)
            ]))
    ])),
    url(r'^test/$', views.test)
)
