from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_configuracionempresa_logo_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE productos CHANGE COLUMN tipo_id tipo_id INT;",
            reverse_sql="",
        ),
    ]
