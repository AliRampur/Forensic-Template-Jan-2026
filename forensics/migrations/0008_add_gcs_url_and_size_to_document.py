"""
Migration to add GCS URL and size fields to Document model,
and index for inventory_unit relationship.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forensics', '0007_document_gcs_path_document_inventory_unit_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='file_url',
            field=models.URLField(
                blank=True,
                help_text='Direct URL to view/download document (may be signed GCS URL)',
                max_length=1000,
            ),
        ),
        migrations.AddField(
            model_name='document',
            name='file_size_bytes',
            field=models.BigIntegerField(
                blank=True,
                null=True,
                help_text='File size in bytes',
            ),
        ),
        migrations.AlterField(
            model_name='document',
            name='inventory_unit',
            field=models.ForeignKey(
                blank=True,
                help_text='Associated inventory unit (for builder invoices)',
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name='builder_documents',
                to='forensics.inventoryunit',
            ),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(
                fields=['inventory_unit'],
                name='forensics_d_invento_idx',
            ),
        ),
    ]
