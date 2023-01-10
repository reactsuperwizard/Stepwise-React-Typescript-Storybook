from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage


class StaticStorage(S3StaticStorage):
    location = 'static'
    file_overwrite = True
    default_acl = 'public-read'


class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = "private"
    querystring_auth = True
