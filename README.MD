# DRF-RemoteJWT

This is a package for the implementation of a remote authentication backend 
primarily meant for use with JWTs but supporting sessions as well. 
The target would be microservice architecture ecosystems.

PyPi package can be found here: https://pypi.org/project/drf-remotejwt/

This package is used in the example 
[auth-client-service-example](https://github.com/garrethcain/auth-client-service-example)
project. 
The package is a wrapper for all the main components of the auth-service; eg.

* /token/ to obtain an access and a refresh token, 
    and create/update the local instance.
* /token/refresh/ to refresh an access token.
* /token/verify/ to confirm if a token is valid or not.

Which all match the auth service exactly. You can decide on the URLs prefix path
by modifying the config/urls.py file appropriately. 

For example;
`path('auth/', include("drf_remotejwt.urls"))` 

... will prefix the `/token/`, `/token/verify/`, and `/token/refresh/` endpoints 
with `/auth/` which gives some clean seperation.

Eg;
```
/auth/token/
/auth/token/refresh/
/auth/token/verify/
```

All you need to is add the drf-remotejwt URLs to your API service that will be 
authing against the remote auth-service.

You can't create users in the local client-service. If you retrieve a different
user from the auth-service you may get integrity errors in that the DRF-RemoteJWT 
package will overwrite your local user with data from the auth-service... 
It will assume your local user was updated in the remote auth-service.

Your project can still use HMAC by implementing one of our HMAC backends. In this
case though, the HAMC keys are local to your project and not the remote 
Auth-Service. So you need to set up your own relationship and from then on, can 
auth using HMAC without connecting to the auth-service at all.
It would be unusual for HMAC keys to operate across services.


## Get Started

Create a basic API Project. 
Then create your first app to contain a view that returns something to indicate
success.
Change DRFs default permission class to IsAuthenticated.

Install package `drf_remotejwt` and add the following to the 
INSTALLED_APPS;

    1. 'rest_framework', # because it is an API.
    2. 'drf_remotejwt', # for the auth backend to access the 
        auth-service.
    3. "custom_user.apps.CustomUserConfig", # because it's easier if your local 
        user model matches the auth service's one.

Add the following config to your settings.py and modify as appropriate.

Assumptions: The auth-service runs on :8000 and the client-server (your API) 
runs on `:8001`
```JSON
REMOTE_JWT = {
    # leave these as the default.
    "AUTH_HEADER_TYPE": "Bearer",
    "AUTH_HEADER_NAME": "Authorization",
    # Where can we reach the auth-Service
    "REMOTE_AUTH_SERVICE_URL": "http://127.0.0.1:8000",
    # The path to login and retrieve a token
    "REMOTE_AUTH_SERVICE_TOKEN_PATH": "/auth/token/",
    # The path to refresh a token
    "REMOTE_AUTH_SERVICE_REFRESH_PATH": "/auth/token/refresh/",
    # The path to verify a token
    "REMOTE_AUTH_SERVICE_VERIFY_PATH": "/auth/token/verify/",
    # The path to get the user object from the remote auth service
    "REMOTE_AUTH_SERVICE_USER_PATH": "/auth/users/{user_id}/",
    # The various JWT claims.
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
```

The actually User object should be left the same as the Auth service's one and any additional data 
should be contained in a related table.

The local user will only be synced with the one in the Auth-Service at login. To ensure requests are as
snappy as possible, any View auth confirmations will only validate the JWT, then use the local user object, if 
it exists, otherwise a new one will be requested if none exists.

Something to think about is that it's possible for the user to authenticate with the auth-service directly, then 
suddenly turn up at your API service and the tokens will be honoured...


If you want your DRF views to authenticate in a browser window, ie. use the session created when you logged in
with either the admin panel or your own login page then add the following to `REST_FRAMEWORK`.

```JSON
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
}
```

Of course, this config should already contain;

```JSON
"drf_remotejwt.authentication.RemoteJWTAuthentication",     # Use our service
```


## TODO:
1. I think the wrapper for the auth endpoints could be implemented better. Maybe a tidy class.
2. There seems to be a bug with Simple-JWT which results in the Authorisation heading not being found.
3. Write something that lets an admin user bring a user from the auth-service into our local service for when they need conf.
