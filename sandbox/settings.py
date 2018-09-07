"""
Django settings for richie project.
"""
import json
import os

from django.utils.translation import ugettext_lazy as _

import raven
from configurations import Configuration, values
from elasticsearch import Elasticsearch

from richie.apps.search.utils.es_indices import IndicesList

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join("/", "data")


def get_release():
    """Get current release of the application

    By release, we mean the latest commit's sha1. Two strategies are tested to
    get this info:

    1. from the version.json file à la Mozilla [1] (if any)
    2. from the git repository (if any)

    If none of those returns the release, it defaults to "NA".

    [1] https://github.com/mozilla-services/Dockerflow/blob/master/docs/version_object.md
    """
    project_dir = os.path.abspath(os.path.join(BASE_DIR, os.pardir))

    # Try to get the current release from the version.json file generated by the
    # CI during the Docker image build
    try:
        with open(os.path.join(project_dir, "version.json")) as version:
            return json.load(version)["commit"]
    except FileNotFoundError:
        pass

    # Get latest commit sha1 from the local git repository
    try:
        return raven.fetch_git_sha(project_dir)
    except raven.exceptions.InvalidGitRepository:
        pass

    # Default: not available
    return "NA"


class ElasticSearchMixin(object):
    """
    Elastic Search configuration mixin

    You may want to override default configuration by setting the following environment
    variable:

    * ES_CLIENT
    """

    ES_CLIENT = Elasticsearch(
        [values.Value("localhost", environ_name="ES_CLIENT", environ_prefix=None)]
    )
    ES_CHUNK_SIZE = 500
    ES_INDICES = IndicesList(
        courses="richie.apps.search.indexers.courses.CoursesIndexer",
        organizations="richie.apps.search.indexers.organizations.OrganizationsIndexer",
        subjects="richie.apps.search.indexers.subjects.SubjectsIndexer",
    )

    ES_DEFAULT_PAGE_SIZE = 10

    COURSE_API_ENDPOINT = "https://www.fun-mooc.fr/fun/api/courses"
    ORGANIZATION_API_ENDPOINT = "https://www.fun-mooc.fr/fun/api/universities"
    SUBJECT_API_ENDPOINT = "https://www.fun-mooc.fr/fun/api/course_subjects"


class DRFMixin(object):
    """
    Django Rest Framework configuration mixin.
    NB: DRF picks its settings from the REST_FRAMEWORK namespace on the settings, hence
    the nesting of all our values inside that prop
    """

    REST_FRAMEWORK = {
        "ALLOWED_VERSIONS": ("1.0",),
        "DEFAULT_VERSION": "1.0",
        "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    }


class Base(DRFMixin, ElasticSearchMixin, Configuration):
    """
    This is the base configuration every configuration (aka environnement) should inherit from. It
    is recommended to configure third-party applications by creating a configuration mixins in
    ./configurations and compose the Base configuration with those mixins.

    It depends on an environment variable that SHOULD be defined:

    * DJANGO_SECRET_KEY

    You may also want to override default configuration by setting the following environment
    variables:

    * DJANGO_SENTRY_DSN
    * ES_CLIENT
    * POSTGRES_DB
    * POSTGRES_HOST
    * POSTGRES_PASSWORD
    * POSTGRES_USER
    """

    SECRET_KEY = values.Value(None)
    DEBUG = False
    ALLOWED_HOSTS = []
    SITE_ID = 1

    # Application definition
    ROOT_URLCONF = "urls"
    WSGI_APPLICATION = "wsgi.application"

    # Database
    DATABASES = {
        "default": {
            "ENGINE": values.Value(
                "django.db.backends.postgresql_psycopg2",
                environ_name="DATABASE_ENGINE",
                environ_prefix=None,
            ),
            "NAME": values.Value(
                "richie", environ_name="POSTGRES_DB", environ_prefix=None
            ),
            "USER": values.Value(
                "fun", environ_name="POSTGRES_USER", environ_prefix=None
            ),
            "PASSWORD": values.Value(
                "pass", environ_name="POSTGRES_PASSWORD", environ_prefix=None
            ),
            "HOST": values.Value(
                "localhost", environ_name="POSTGRES_HOST", environ_prefix=None
            ),
            "PORT": values.Value(
                5432, environ_name="POSTGRES_PORT", environ_prefix=None
            ),
        }
    }
    MIGRATION_MODULES = {}

    # Static files (CSS, JavaScript, Images)
    STATIC_URL = "/static/"
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(DATA_DIR, "media")
    STATIC_ROOT = os.path.join(DATA_DIR, "static")
    STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

    # Internationalization
    TIME_ZONE = "Europe/Paris"
    USE_I18N = True
    USE_L10N = True
    USE_TZ = True

    # Templates
    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [os.path.join(BASE_DIR, "templates")],
            "OPTIONS": {
                "context_processors": [
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                    "django.template.context_processors.i18n",
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.template.context_processors.media",
                    "django.template.context_processors.csrf",
                    "django.template.context_processors.tz",
                    "sekizai.context_processors.sekizai",
                    "django.template.context_processors.static",
                    "cms.context_processors.cms_settings",
                ],
                "loaders": [
                    "django.template.loaders.filesystem.Loader",
                    "django.template.loaders.app_directories.Loader",
                    "django.template.loaders.eggs.Loader",
                ],
            },
        }
    ]

    MIDDLEWARE_CLASSES = (
        "cms.middleware.utils.ApphookReloadMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "cms.middleware.user.CurrentUserMiddleware",
        "cms.middleware.page.CurrentPageMiddleware",
        "cms.middleware.toolbar.ToolbarMiddleware",
        "cms.middleware.language.LanguageCookieMiddleware",
    )

    INSTALLED_APPS = (
        # Django
        "djangocms_admin_style",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.admin",
        "django.contrib.sites",
        "django.contrib.sitemaps",
        "django.contrib.staticfiles",
        "django.contrib.messages",
        # Django-cms
        "cms",
        "cmsplugin_plain_text",
        "menus",
        "sekizai",
        "treebeard",
        "djangocms_text_ckeditor",
        "filer",
        "easy_thumbnails",
        "djangocms_column",
        "djangocms_link",
        "djangocms_style",
        "djangocms_snippet",
        "djangocms_googlemap",
        "djangocms_video",
        "djangocms_picture",
        # Richie stuff
        "richie",
        "richie.apps.core",
        "richie.apps.courses",
        "richie.apps.persons",
        "richie.apps.search",
        "richie.plugins.large_banner",
        "richie.plugins.section",
        "richie.plugins.simple_text_ckeditor",
        # Third party apps
        "raven.contrib.django.raven_compat",
        "parler",
    )

    # Group to add plugin to placeholder "Content"
    FUN_PLUGINS_GROUP = "Fun Plugins"

    LANGUAGE_CODE = "en"
    # Careful! Languages should be ordered by priority, as this tuple is used to get
    # fallback/default languages throughout the app.
    # Use "en" as default as it is the language that is most likely to be spoken by any visitor
    # when their preferred language, whatever it is, is unavailable
    LANGUAGES = (("en", _("English")), ("fr", _("French")))
    LANGUAGES_DICT = dict(LANGUAGES)
    LANGUAGE_NAME = LANGUAGES_DICT[LANGUAGE_CODE]

    # Django CMS settings
    CMS_LANGUAGES = {
        "default": {
            "public": True,
            "hide_untranslated": False,
            "redirect_on_fallback": True,
            "fallbacks": ["en", "fr"],
        },
        1: [
            {
                "public": True,
                "code": "en",
                "hide_untranslated": False,
                "name": _("English"),
                "fallbacks": ["fr"],
                "redirect_on_fallback": True,
            },
            {
                "public": True,
                "code": "fr",
                "hide_untranslated": False,
                "name": _("French"),
                "fallbacks": ["en"],
                "redirect_on_fallback": True,
            },
        ],
    }

    PARLER_LANGUAGES = CMS_LANGUAGES

    CMS_TEMPLATES = (
        ("courses/cms/course_detail.html", _("Course page")),
        ("courses/cms/organization_detail.html", _("Organization page")),
        ("courses/cms/subject_detail.html", _("Subject page")),
        ("persons/cms/person_detail.html", _("Person page")),
        ("search/search.html", _("Search")),
        ("richie/fullwidth.html", "Fullwidth"),
        ("richie/child_pages_list.html", _("List of child pages")),
        ("richie/child_courses_list.html", _("List of child courses")),
    )
    CMS_PERMISSION = True

    CMS_PLACEHOLDER_CONF = {
        # Course detail
        "courses/cms/course_detail.html course_cover": {
            "name": _("Course cover"),
            "plugins": ["PicturePlugin"],
            "limits": {"PicturePlugin": 1},
        },
        "courses/cms/course_detail.html course_teaser": {
            "name": _("Course teaser"),
            "plugins": ["VideoPlayerPlugin", "PicturePlugin"],
            "limits": {"VideoPlayerPlugin": 1, "PicturePlugin": 1},
        },
        "courses/cms/course_detail.html course_syllabus": {
            "name": _("Course Syllabus"),
            "plugins": ["CKEditorPlugin"],
        },
        "courses/cms/course_detail.html course_format": {
            "name": _("Format"),
            "plugins": ["CKEditorPlugin"],
        },
        "courses/cms/course_detail.html course_prerequisites": {
            "name": _("Prerequisites"),
            "plugins": ["CKEditorPlugin"],
        },
        "courses/cms/course_detail.html course_team": {
            "name": _("Course team"),
            "plugins": ["PersonPlugin"],
        },
        "courses/cms/course_detail.html course_plan": {"name": _("Course plan")},
        "courses/cms/course_detail.html course_information": {
            "name": _("Complementary information"),
            "plugins": ["SectionPlugin"],
        },
        "courses/cms/course_detail.html course_license_content": {
            "name": _("License for the course content"),
            "plugins": ["LicencePlugin"],
            "limits": {"LicencePlugin": 1},
        },
        "courses/cms/course_detail.html course_license_participation": {
            "name": _("License for the content created by course participants"),
            "plugins": ["LicencePlugin"],
            "limits": {"LicencePlugin": 1},
        },
        # Organization detail
        "courses/cms/organization_detail.html banner": {
            "name": _("Banner"),
            "plugins": ["PicturePlugin"],
            "limits": {"PicturePlugin": 1},
        },
        "courses/cms/organization_detail.html logo": {
            "name": _("Logo"),
            "plugins": ["PicturePlugin"],
            "limits": {"PicturePlugin": 1},
        },
        "courses/cms/organization_detail.html description": {
            "name": _("Description"),
            "plugins": ["CKEditorPlugin"],
            "limits": {"CKEditorPlugin": 1},
        },
        # Subject detail
        "courses/cms/subject_detail.html banner": {
            "name": _("Banner"),
            "plugins": ["PicturePlugin"],
            "limits": {"PicturePlugin": 1},
        },
        "courses/cms/subject_detail.html logo": {
            "name": _("Logo"),
            "plugins": ["PicturePlugin"],
            "limits": {"PicturePlugin": 1},
        },
        "courses/cms/subject_detail.html description": {
            "name": _("Description"),
            "plugins": ["CKEditorPlugin"],
            "limits": {"CKEditorPlugin": 1},
        },
        # Person detail
        "persons/cms/person_detail.html portrait": {
            "name": _("Portrait"),
            "plugins": ["PicturePlugin"],
            "limits": {"PicturePlugin": 1},
        },
        "persons/cms/person_detail.html resume": {
            "name": _("Resume"),
            "plugins": ["CKEditorPlugin"],
            "limits": {"CKEditorPlugin": 1},
        },
    }

    # CKEditor available settings
    CKEDITOR_SETTINGS = {
        "language": "{{ language }}",
        "skin": "moono-lisa",
        "toolbarCanCollapse": False,
        "contentsCss": "/static/css/ckeditor.css",
        # Enabled showblocks as default behavior
        "startupOutlineBlocks": True,
        # Enable some plugins
        # 'extraPlugins': 'codemirror',
        # Disable element filter to enable full HTML5, also this will let
        # append any code, even bad syntax and malicious code, so be careful
        "removePlugins": "stylesheetparser",
        "allowedContent": True,
        # Image plugin options
        "image_prefillDimensions": False,
        # Justify text using shortand class names
        "justifyClasses": ["text-left", "text-center", "text-right"],
        # Default toolbar configurations for djangocms_text_ckeditor
        "toolbar": "CMS",
        "toolbar_CMS": [
            ["Undo", "Redo"],
            ["ShowBlocks"],
            ["Format", "Styles"],
            ["RemoveFormat"],
            ["Maximize"],
            "/",
            ["Bold", "Italic", "Underline", "-", "Subscript", "Superscript"],
            ["JustifyLeft", "JustifyCenter", "JustifyRight"],
            ["Link", "Unlink"],
            [
                "Image",
                "-",
                "NumberedList",
                "BulletedList",
                "-",
                "Table",
                "-",
                "CreateDiv",
                "HorizontalRule",
            ],
            ["Source"],
        ],
    }
    # Share the same config for djangocms_text_ckeditor field and derived
    # CKEditor widgets/fields
    CKEDITOR_SETTINGS["toolbar_HTMLField"] = CKEDITOR_SETTINGS["toolbar_CMS"]

    # Thumbnails settings
    THUMBNAIL_PROCESSORS = (
        "easy_thumbnails.processors.colorspace",
        "easy_thumbnails.processors.autocrop",
        "filer.thumbnail_processors.scale_and_crop_with_subject_location",
        "easy_thumbnails.processors.filters",
        "easy_thumbnails.processors.background",
    )

    # Sentry
    #
    # Nota bene: the DJANGO_SENTRY_DSN environment variable should be defined to
    # report failures to Sentry
    RAVEN_CONFIG = {
        "dsn": values.Value(environ_name="SENTRY_DSN"),
        "release": get_release(),
        "environment": values.Value(environ_name="CONFIGURATION"),
    }

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": True,
        "root": {"level": "WARNING", "handlers": ["sentry"]},
        "formatters": {
            "verbose": {
                "format": "%(levelname)s %(asctime)s %(module)s "
                "%(process)d %(thread)d %(message)s"
            }
        },
        "handlers": {
            "sentry": {
                "level": "ERROR",  # To capture more than ERROR, change to WARNING, INFO, etc.
                "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
                "tags": {"custom-tag": "x"},
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "django.db.backends": {
                "level": "ERROR",
                "handlers": ["console"],
                "propagate": False,
            },
            "raven": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
            "sentry.errors": {
                "level": "DEBUG",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }


class Development(Base):
    """
    Development environment settings

    We set DEBUG to True and configure the server to respond from all hosts.
    """

    DEBUG = True
    ALLOWED_HOSTS = ["*"]


class Test(Base):
    """Test environment settings"""

    pass


class ContinuousIntegration(Test):
    """
    Continous Integration environment settings

    nota bene: it should inherit from the Test environment.
    """

    pass


class Production(Base):
    """Production environment settings

    You must define the DJANGO_ALLOWED_HOSTS environment variable in Production
    configuration (and derived configurations):

    DJANGO_ALLOWED_HOSTS="foo.com,foo.fr"
    """

    ALLOWED_HOSTS = values.ListValue(None)

    # For static files in production, we want to use a backend that includes a hash in
    # the filename, that is calculated from the file content, so that browsers always
    # get the updated version of each file.
    STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    )


class Feature(Production):
    """
    Feature environment settings

    nota bene: it should inherit from the Production environment.
    """

    pass


class Staging(Production):
    """
    Staging environment settings

    nota bene: it should inherit from the Production environment.
    """

    pass


class PreProduction(Production):
    """
    Pre-production environment settings

    nota bene: it should inherit from the Production environment.
    """

    pass
