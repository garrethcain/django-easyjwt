from django import VERSION

if VERSION < (3, 2):
    default_app_config = "remotejwt_auth.token_blacklist.apps.TokenBlacklistConfig"
