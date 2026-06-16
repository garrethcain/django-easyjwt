from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("easyjwt_user", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="jwt_secret",
        ),
    ]
