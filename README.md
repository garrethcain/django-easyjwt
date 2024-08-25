# Django-EasyJWT

This is a package for the implementation of a remote authentication backend
for Django apps, primarily meant for use with JWTs, also supporting sessions as
well. Ie. elevated users could log into the Django `/admin/` once authenticated.
The target is microservice ecosystems, with several independant services all
authenticating against a central authentication services, or cas.

The PyPi package can be found here: https://pypi.org/project/django-easyjwt

ACKNOWLEDGEMENTS
This package is heavily based on Djangorestframework_simplejwt and heavily influenced by SimpleJWT.

This package is used in the example
[auth-client-service-example](https://github.com/garrethcain/django-easyjwt-example)
project.

# Change Log

2024-03-19 - 4.0.2
    - removed dependency from remotejwt_user migrations.
    - added raw_data to the context var of the custom serializer so custom data stripped by the serializer
      can still be accessed.
    - Changed the exception raise for a remote user model to show text and not try parse to json.

# How To

There are, at a minimum, two components required for this to work;

1. An Auth-Service, to authenticate against,
2. A Client-Service, users want to use.

This package is made of of three sub-packages; RemoteJWT-Auth, RemoteJWT-Client, and RemoteJWT-User.
With the Auth & Client used in the separate Auth and Client services and the User being used in both,
or neither.

The idea being that you can have any number of client-services using the same
auth-service to validate login requests and your auth-service is behind some
kind of private network and not public facing.

This package is a wrapper for all the main components of the auth-service and client-service; eg.

* /token/ to obtain an access and a refresh token,
    and create/update the local instance.
* /token/refresh/ to refresh an expired access token.
* /token/verify/ to confirm if a token is valid or not.

The above urls in the client-service just proxy requests to the remote
Auth-Service, configured in `settings.py` `REMOTE_JWT` dict, but creating a
local user object if required.

All that is needed is to add the Django-EasyJWT URLs to your client-service. The
auth-service remains mostly vanilla aside from maybe using a custom User model,
include in this package as well, for convenience.

You can't create users in the local client-service!
If you retrieve a user from the auth-service with the same ID you will overwrite
the local record with data from the auth-service.

Your project can use HMAC by implementing some HMAC backend locally. The HMAC
keys will be kept local to the service and not centralised in the Auth-Service.
The Auth-Service is intentionally kept lean and only handles "users".


# Get Started

What we'll be doing;

1. Create an Auth-Service
2. Create a Client-Service



## Create an Auth-Service

Always upgrade pip first.
```
$ pip install --upgrade pip
```

Create a temporary virtual environment to install django so we can create a
project.
```
$ python -m virtualenv .venv
```

Activate the virtual environment.
```
$ source .venv/bin/activate
```

Your terminal should look something like this;

`(.venv)  user@domain  ~/Code/ `

With the `(.venv)` part implying you're currently inside a virtual environment.

Install Django so we can create our app.
```
$ pip install django
```

Create our project with the name `config` so the nested directory is named more
conveniently.
```PYTHON
$ django-admin startproject config
```

Rename the outer directory because I personally like having the project's config
kept in a directory called `config` with the outer directory the name of
project.
```PYTHON
$ mv config auth-service
```

You should have a directory structure similar to this.
```
─── auth-service
    ├── config
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── manage.py
```

Now let's remove the temp virtual environment by deactivating, deleting the old
one, then creating a new on in the right place.
```
$ deactivate
```

Your terminal should be back to something like this;
`user@domain  ~/Code/ `

Delete the files.
```
$ rm -Rf .venv
```

```
$ cd auth-service
```

Create another virtual environment.
```
$ python -m virtualenv .venv
```

Activate the virtual environment, again. We'll keep this one this time.
```
$ source .venv/bin/activate
```

Again, your terminal should look something like this;
`(.venv)  user@domain  ~/Code/auth-service/ `

Install the packages we're going to use.
```
$ pip install django django_rest_framework django_easyjwt
```

Open `config/settings.py` and add the apps we'll be using to `INSTALLED_APPS`;

```PY
INSTALLED_APPS = [
    ...
    'rest_framework',
    'remotejwt_auth',
    'remotejwt_user',
]
```

We've included `remotejwt_user` so we can use the same User model between
all services. It also includes some convieniences such as update forms and
changes the Username field from `username` to `email`.

Tell Django about the new user model by adding;
```py
AUTH_USER_MODEL = "remotejwt_user.User"
```

Next we need to configure Django Rest Framework. For this example you need just
the following;
```PYTHON
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "remotejwt_auth.authentication.JWTAuthentication",
    ),
}
```

In order to use RemoteJWT-Auth you will also need to add some configuration for it.

```PY
REMOTE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": "d577273ff885c3f84dadb8578bb40000", # You must set this correctly for Production.
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "remotejwt_auth.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("remotejwt_auth.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "remotejwt_auth.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}
```

In the JWT configuration we use `timedelta` so you need to import `timedelta` at
the top of `config/settings.py`.

`from datetime import timedelta`

Make migrations so we can migrate.
```
$ python manage.py makemigrations
```

Migrate to create the database. An SQLite db is fine for the example. In a
production environment you'd use something a bit more appropriate like PostreSQL or DynamoDB.
```
$ python manage.py migrate
```

And finally you can stand up the auth-service with;
```
$ python manage.py runserver
```

Which should get you something like;
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
May 02, 2023 - 10:50:48
Django version 4.0.2, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

Hit `^C` so we can create a few users for testing with later on.

We're going to create three test users as below.
* admin | admin@test.com | admin-pass
* staff | staff@test.com | staff-pass
* user | user@test.com | user-pass

Eg.
```
export DJANGO_SUPERUSER_EMAIL=admin@test.com
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin-pass
python manage.py createsuperuser --noinput
```
or
```
$ python manage.py createsuperuser
```
Then stand up the auth-service and log into `http://127.0.0.1:8000/admin/` login
with the superuser you created above and create the other two users, setting
`is_staff=True` for the staff user.
Log out once you're done and terminate the instance that's running with `^C` and
deactivate this virtual environment.
```
$ deactivate
```

The final step is to configure the Urls. So open `config/urls.py` and add the
following.

Then expost the paths to the JWT endpoints and a user view which is where the
client-service will download the user from.
```py
urlpatterns = [
    ...
    path('auth/', include('remotejwt_auth.urls')),  # gives us access to the auth views.
    path('auth/', include('remotejwt_user.urls')),  # gives us access to the users views.
]
```

And that's it for the Auth-Service. It doesn't need any views or serializers.
Everything is handled by RemoteJWT-Auth and Django's OEM methods. This service is
super light to run and will handle many requests with ease.

---
## Create a Client-Service

Now we need a client-service that will authenticate against the Auth-Service to
complete the example.

Go up one directory;
```
cd ..
```

We're going to perform the same steps for the client-service that we did for the
auth-service. You should recognise most of this. The main difference is that
this time we'll be using `django_easyjwt` and not creating any local users.


Create a temporary virtual environment to install django so we can create a
project.
```
$ python -m virtualenv .venv
```

Activate the virtual environment.
```
$ source .venv/bin/activate
```

Your terminal should look something like this;

`(.venv)  user@domain  ~/Code/ `

With the `(.venv)` part implying you're currently inside a virtual environment.

Install Django so we can create our app.
```
$ pip install django
```

Create our project with the name `config` so the nested directory is named more
conveniently.
```PYTHON
$ django-admin startproject config
```

Rename the outer directory because I personally like having the project's config
kept in a directory called `config` with the outer directory the name of
project.
```PYTHON
$ mv config client-service
```

You should have a directory structure similar to this.
```
├── auth-service
│   ├── config
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── db.sqlite3
│   └── manage.py
└── client-service
    ├── config
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── manage.py
```

Now let's remove the temp virtual environment by deactivating, deleting the old
one, then creating a new on in the right place.
```
$ deactivate
```

Your terminal should be back to something like this;
`user@domain  ~/Code/ `

Delete the files.
```
$ rm -Rf .venv
```

```
$ cd client-service
```

Create another virtual environment.
```
$ python -m virtualenv .venv
```

Activate the virtual environment, again. We'll keep this one this time.
```
$ source .venv/bin/activate
```

Again, your terminal should look something like this;
`(.venv)  user@domain  ~/Code/auth-service/ `

Install the packages we're going to use. We don't need `SimpleJWT` this time
because authentication is handled by the remote auth-service.
```
$ pip install django django_rest_framework django_easyjwt
```

We need to let Django know about the apps we'll be using, so open `settings.py`
and add the following lines to `INSTALLED_APPS`;
```PY
INSTALLED_APPS = [
    ...
    'rest_framework',
    'remotejwt_client',
    'remotejwt_user',
]
```

We need to use the same User model as the auth-service, otherwise the user
returned by the auth-service will cause an integrity error.

```py
AUTH_USER_MODEL = "remotejwt_user.User"
```

Add some configuration for Djang Rest Framework. Change the default behaviour
for all endpoints to require authentication. Then we override the default
authentication classes with the ones from `Django-EasyJWT`.
```py
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "remotejwt_client.authentication.RemoteJWTAuthentication",     # Use our service
        "rest_framework.authentication.SessionAuthentication",  # Maybe the user has a session...
    ),
}
```

Let Django know that we want to use a custom authentication backend.
```py
# implement out or custom backend for Admin and other views.
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',    # Default, check the local DB.
    'remotejwt_client.authentication.ModelBackend'         # Our override to check the remote service.
]
```

Time to configure `Django-EasyJWT`. For this example example we're going to run
the auth-server on `:8000` and the client-service on `:8001`. Most of this conf
should be handled through environmental variables in a real project. But we're
just aiming for the absolute minimal working example.

```py
REMOTE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer", ),
    "AUTH_HEADER_NAME": "Authorization",
    "REMOTE_AUTH_SERVICE_URL": "http://127.0.0.1:8000", # Where do we reach the Auth-Service
    "REMOTE_AUTH_SERVICE_TOKEN_PATH": "/auth/token/", # The path to login and retrieve a token
    "REMOTE_AUTH_SERVICE_REFRESH_PATH": "/auth/token/refresh/", # The path to refresh a token
    "REMOTE_AUTH_SERVICE_VERIFY_PATH": "/auth/token/verify/", # The path to verify a token
    "REMOTE_AUTH_SERVICE_USER_PATH": "/auth/users/{user_id}/", # The path to get the user object
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
```

Open `config/urls.py` and add the URLs from RemoteJWT that will be passed
through to the auth-service.

```py
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include("remotejwt_client.urls"))
]
```
Don't forget the `include` import.

We'll add our test view to the urls as well shortly.

All the client-service needs now is an endpoint to prove it's alive. So let's
add a Django app with a view that requires authentication we use to test.
```py
$ django-admin startapp test_app
```

Your directory structure should now look something along the lines of;
```
.
├── config
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
└── test_app
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── migrations
    │   └── __init__.py
    ├── models.py
    ├── tests.py
    └── views.py
```

You can see the new app called `test_app` has been added.

Open `test_app/views.py` and add the following view. Because we changed the
Rest Framework config to use a `DEFAULT_PERMISSION_CLASSES` of `IsAuthenticated`
all views will require authentication.
```py
from rest_framework import generics
from rest_framework.response import Response

class TestView(generics.GenericAPIView):
    def get(self, request):
        return Response("success", status=200)
```

There are no models or serializers, it's the absolute least we can do to get a
success. There is no need to add the `test_app` to the `INSTALLED_APPS` because
it has no models that need migrating.


The absolute final step before we can run some tests is to add the `TestView` to
the client-service's Urls.py so it knows where to send an incoming request.

```py
from django.urls import path, include
from test_app.views import TestView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include("remotejwt_client.urls")),
    path('api/test/', TestView.as_view()),
]
```

Don't forget it include the `include` import at the end of
`from django.urls import path` at the top of the `urls.py` file.

Modfiy the `config/urls.py` so it looks like the above.
First we import the `TestView` from `test_app` and then we give it a path, in
this case `/api/test/`.

Let's migrate the client-service so it has a database to write the user to.
```
$ python manage.py makemigrations
```
```
$ python manage.py migrate
```



## Standing up the Services

As mentioned earlier, we have two services and auth-service and a client-service
. We want the auth-service to be on `:8000` and the client-service to be at
`:8001`.

**This is important because it's how we configure the RemoteJWT's configuration
in the auth-service and client-service.**

You'll need two terminals. One in auth-service/ and one in client-service/ both
with the respective virtual environments loaded and then a third one to execute
the requests from using `curl`.

In auth-service, stand up on port `:8000` like;
```
(.venv)  user@domain > ~/Code/auth-service $ python manage.py runserver 0.0.0.0:8000
```

And then stand up the client-service on port `:8001` like this;
```
(.venv)  user@domain > ~/Code/client-service $ python manage.py runserver 0.0.0.0:8001
```

---

# How to test the API

In the below examples we're mking requests to super simple API  (client-service)
which will reach out to the auth-service to retrieve, verify, and if needed
refresh the tokens.

You can check the client-service's db.sqlite3 database before making any
requests to confirm the `user` table is empty. After making a few successful
requests there will be some users there.

Remember the users added to the auth-service further back?
You'll need those email and passwords shortly.

Also remember that the auth-service is at `:8000` and the client-service is at
`:8001`. As a client-service user, we should never interact with the
auth-service directly. It shouldn't even be accessible to the public in a normal
production environment.

## Authorise and obtain a token pair

```
curl \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email": "user@test.com", "password": "user-pass"}' \
  http://127.0.0.1:8001/auth/token/
```

Will give you a response like;
```JSON
{
    "refresh":" ... ",
    "access":" ... "
}
```

(I removed the tokens above for brevity.)


## Perform a generic API requst

Export the access token from the previous response to an envar.
eg.
 `export ACCESS_TOKEN={paste_token_here}`

 Should return 'success'.

```
curl \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  http://127.0.0.1:8001/api/test/
```

The response should be;

```JSON
    "success"
```


## Refresh an expired token

```
curl \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"refresh": "${REFRESH_TOKEN"}}' \
  http://127.0.0.1:8001/auth/token/refresh/
```


## Verify the token is correct
 Performed by the client-service against the auth-service with every single
 JWT API request.

```
curl \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"token": "${REFRESH_TOKEN}"}' \
  http://127.0.0.1:8001/auth/token/verify/
```


## Get the user details
This would be done inside the Auth handler when the user doesn't exist. There
needs to be a valid user_id for the user associated with the access token being
used. Ie. you can't view other user objectss by guessing an ID. Only your own.

```
curl \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  http://localhost:8001/auth/users/{user_id}/
```


# Exta Data

There may be situations where you want the Auth-Service to include additional User information that is passed
down to the Client-Services. One scenario for this may be having a centralised auth service, but customer's
subscribe to the client services individually; this means a user may have access to service A but not service
B.

This can easily be achieved by specifying and creating custom User Model Serializers. The config key for this
is "USER_MODEL_SERIALIZER" where you specify a serializer to use when parsing the User data returned from the
Auth-Service, eg. "custom.serializers.CustomUserModelSerialzer".

The Auth-Service serializer needs to expose ALL the data that will be needed by ALL Client-services. A Client-
service needs to only parse the data relevant to it.
I.e. it is possible to Client-services to have different custom serializers only recording the fields they
individually care about.

```python
class CustomUserFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUserField
        fields = ("field1", "field2", "field3")
```

```python
class CustomUserModelSerializer(serializers.ModelSerializer):
    customuserfield = CustomUserFieldSerializer()

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "email",
            "last_name",
            "date_joined",
            "last_login",
            "is_active",
            "is_staff",
            "is_superuser",
            "customuserfield",
        )
        # any read_only fields here will remove them from the validate_data stopping them from being updated
        # in the client db.

    def create(self, validated_data):
        """
        DRF doesn't support nested serializers so we need to create the nested
        objects manually.
        """

        user_id = validated_data.pop(USERNAME_FIELD)
        customuserfield = validated_data.pop("customuserfield")
        user, _ = User.objects.get_or_create(email=user_id, defaults=validated_data)
        # Delete stale customuserfield data.
        # It's stale because this payload is the latest truth.
        user.customuserfield.delete()

        serializer = CustomUserFieldSerializer(data=customuserfield)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)

        return user

    def update(self, instance, validated_data):
        customuserfield = validated_data.pop("customuserfield")
        # Delete stale customuserfield data.
        # It's stale because this payload is the most recent truth.
        instance.customuserfield.delete()
        serializer = CustomUserFieldSerializer(data=customuserfield)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=instance)

        instance.first_name = validated_data["first_name"]
        instance.last_name = validated_data["last_name"]
        # Do no update email, its a primary key.
        instance.last_login = validated_data["last_login"]
        instance.is_active = validated_data["is_active"]
        instance.is_staff = validated_data["is_staff"]
        instance.is_superuser = validated_data["is_superuser"]
        instance.save()
        return instance
```

Because, in this example, the extra data is being exposed as a nested serializer, you are required to override
the serializers .create() method and handle the nested data yourself. This give the flexability to only record
the data relevant to the service.


# Permissions
Now that some custom data is being sent along witht the login request, we need to do something with it that
allows a user to use one service and not another. The most straight forward solution would be to name the
fields being passed as the services needing access and then use a permission class (for DRF only) to reject
access if they're not authed for this particular service.


```python
from rest_framework import permissions


class CustomAccessPermission(permissions.BasePermission):
    message = "You do not have permission to this service"

    def has_object_permission(self, request, view, obj):
        return request.user is not None

    def has_permission(self, request, view):
        return request.user.customuserfield.field1 == "field1 value"
```
