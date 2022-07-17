# Generated by Django 4.0.5 on 2022-07-16 19:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import filer.fields.image


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        migrations.swappable_dependency(settings.FILER_IMAGE_MODEL),
        ('genericsite', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='base_template',
            field=models.CharField(blank=True, max_length=255, verbose_name='base template'),
        ),
        migrations.AlterField(
            model_name='article',
            name='content_template',
            field=models.CharField(blank=True, max_length=255, verbose_name='content body template'),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='admin_name',
            field=models.CharField(help_text='Name used in the admin to distinguish from other home pages', max_length=255, unique=True, verbose_name='admin name'),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='base_template',
            field=models.CharField(blank=True, max_length=255, verbose_name='base template'),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='content_template',
            field=models.CharField(blank=True, max_length=255, verbose_name='content body template'),
        ),
        migrations.AlterField(
            model_name='page',
            name='base_template',
            field=models.CharField(blank=True, max_length=255, verbose_name='base template'),
        ),
        migrations.AlterField(
            model_name='page',
            name='content_template',
            field=models.CharField(blank=True, max_length=255, verbose_name='content body template'),
        ),
        migrations.AlterField(
            model_name='section',
            name='base_template',
            field=models.CharField(blank=True, max_length=255, verbose_name='base template'),
        ),
        migrations.AlterField(
            model_name='section',
            name='content_template',
            field=models.CharField(blank=True, max_length=255, verbose_name='content body template'),
        ),
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admin_name', models.CharField(max_length=255, verbose_name='admin name')),
                ('slug', models.SlugField(verbose_name='slug')),
                ('title', models.CharField(blank=True, max_length=255, verbose_name='title')),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sites.site', verbose_name='site')),
            ],
            options={
                'unique_together': {('site', 'slug')},
            },
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(help_text='This can be either an absolute path or a full URL starting with a scheme such as “https://”.', max_length=255, verbose_name='URL')),
                ('title', models.CharField(blank=True, max_length=255, verbose_name='title')),
                ('custom_icon', models.CharField(blank=True, help_text='<a href=https://icons.getbootstrap.com/#icons target=iconlist>icon list</a>', max_length=50, verbose_name='custom icon')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('menu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='genericsite.menu', verbose_name='menu')),
                ('og_image', filer.fields.image.FilerImageField(blank=True, help_text='Image for social sharing', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.FILER_IMAGE_MODEL)),
            ],
            options={
                'unique_together': {('menu', 'title'), ('menu', 'url')},
            },
        ),
    ]
