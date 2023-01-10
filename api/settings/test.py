from settings.base import *  # noqa

HAYSTACK_SIGNAL_PROCESSOR = "apps.core.haystack.SyncCelerySignalProcessor"

KIMS_API_REQUEST_RATE = "1000000/s"

LOGGING = {
    **LOGGING,  # type: ignore # noqa
    "loggers": {
        **LOGGING["loggers"],  # type: ignore # noqa
        "vcr": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
