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
`path('auth/', include("remotejwt.urls"))` 

... will prefix the `/token/`, `/token/verify/`, and `/token/refresh/` endpoints 
with `/auth/` which gives some clean seperation.

Eg;
```PYTHON
/auth/token/
/auth/token/refresh/
/auth/token/verify/
```

All you need to is add the DRF-RemoteJWT URLs to your API service that will be 
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
Then create your first app to contain a view that returns something indicating a
success.
Change DRFs default permission class to IsAuthenticated.

Install package `remotejwt` and add the following to the INSTALLED_APPS;

```PYTHON
INSTALLED_APPS = [
    ...
    'rest_framework', # because it is an API.
    'remotejwt', # for the auth backend to access the auth-service.
    ...
]
```

Add the following config to your settings.py and modify as appropriate.

Assumptions: The auth-service runs on :8000 and the client-service (your API) 
runs on `:8001`


## Add this configuration to the client-service `settings.py`;

Instruct `REST_FRAMEWORK` that it must use the `remotejwt` module for
authentication.

```PYTHON
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        'remotejwt.authentication.RemoteJWTAuthentication',
    ),
}
```

```PYTHON
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

The actual User object should be left the same as the Auth service's one and any
additional data should be contained in a related table.

The local user will only be synced with the one in the Auth-Service at login. To
ensure requests are as snappy as possible, any View auth confirmations will only
validate the JWT, then use the local user object, if it exists, otherwise a new
one will be requested if none exists.

Something to think about is that it's possible for the user to authenticate with
the auth-service directly, then suddenly turn up at your API service and the
tokens will be honoured...

A custom user `remotejwt_user` has been include in the model and can be used in
both the client-service and auth-service for convenience. To use it simply add
the following config.

```PYTHON
INSTALLED_APPS = [
    ...
    'remotejwt_user.User',
    ...
]
```

```PYTHON
AUTH_USER_MODEL = "remotejwt_user.User"
```

And then in your auth-service you can import the end points from the package
like this;

auth_service.urls.py
```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path('auth/',
         include(
            [
                path('', include('remotejwt.urls')),
                path('', include('remotejwt_user.urls')),
            ]
        )
    )
]
```

or add them in yourself for a bit more control;

```python
from remotejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from remotejwt_user.views import TokenUserDetailView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/users/<int:pk>/", TokenUserDetailView.as_view(), name="user_detail"),
]
```


If you want your DRF views to authenticate in a browser window, ie. the session
created when you logged in with either the admin panel or your own login page
then additionally add `rest_framework.authentication.SessionAuthentication` to
`DEFAULT_AUTHENTICATION_CLASSES` inside `REST_FRAMEWORK`.

Eg.
```PYTHON
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        'remotejwt.authentication.RemoteJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        ...
    ),
}
```

## TODO:
1. I think the wrapper for the auth endpoints could be implemented better. Maybe
    a tidy class.
2. There seems to be a bug with Simple-JWT which results in the Authorisation
    heading not being found.
3. Write something that lets an admin user bring a user from the auth-service
    into our local service for when they need conf.
4. Implement a custom user model for convenience.
5. Rename the module itself to remove the hyphen.