
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pharmacy", "0012_alter_medicine_unit"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # created_at already exists physically in MySQL.
            # Add only the missing updated_at column.
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE pharmacy_pharmacysaleitem
                        ADD COLUMN updated_at DATETIME(6)
                        NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                        ON UPDATE CURRENT_TIMESTAMP(6)
                    """,
                    reverse_sql="""
                        ALTER TABLE pharmacy_pharmacysaleitem
                        DROP COLUMN updated_at
                    """,
                ),
            ],

            # Restore both fields to Django's migration state.
            state_operations=[
                migrations.AddField(
                    model_name="pharmacysaleitem",
                    name="created_at",
                    field=models.DateTimeField(auto_now_add=True),
                ),
                migrations.AddField(
                    model_name="pharmacysaleitem",
                    name="updated_at",
                    field=models.DateTimeField(auto_now=True),
                ),
            ],
        ),
    ]
