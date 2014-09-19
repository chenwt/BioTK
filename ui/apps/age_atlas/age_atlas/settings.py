from django.conf import settings

BOWER_INSTALLED_APPS = (
    "jquery",
    "bootstrap#3.2.0",
    "datatables-tabletools#2.2.3",
    "nvd3#1.1.15-beta"
)

INSTALLED_APPS = (
    "age_atlas",
    "djangobower"
)

STATICFILES_FINDERS = (
    'djangobower.finders.BowerFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
)

def configure(mod):
    for k,v in globals().items():
        if k.isupper():
            v = tuple(set(getattr(mod, k, tuple()) + v))
            setattr(mod, k, v)
