"""Database table definitions for the application, everything is logging related."""
import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models


class BaseModel(models.Model):
    """BaseModel that is inherited from every model. Includes basic information."""

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Application(BaseModel):
    """
    Table for every application that might be used

    - this is not created get_or_create,
    so it is not yet a full representation of every application installed,
    this might follow
    """

    name = models.CharField(max_length=255)

    def __str__(self):
        """Returns name of application."""
        return self.name


class Field(BaseModel):
    """
    Table definition for a regular field.

    Is tied to a ContentTypes.
    If the model will be deleted all the related fields will be therefor too.
    """

    name = models.CharField(max_length=255)
    model = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE, related_name='dal_field')

    def __str__(self):
        return 'Table {}, Field {}'.format(self.model, self.name)


class ModelObject(BaseModel):
    """
    BaseObject of the system.

    BaseObject for everything logging related.
    consists of a value: gathered through repr()
    field - which is a definition of the field
    and if it refers to a relationship the model.
    """

    value = models.CharField(max_length=255, null=True)
    field = models.ForeignKey(Field, null=True, on_delete=models.CASCADE)
    type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE, related_name='atl_modelobject_application')

    def __str__(self):
        output = '{}'.format(self.value)

        if self.field is not None:
            output = "{}, Value: {}".format(self.field, self.value)

        if self.type is not None:
            output = "Table: {}.{}, Row: {}".format(self.type.app_label, self.type.model, self.value)

        return output


class ModelModification(BaseModel):
    """Saves the two states of several fields."""

    previously = models.ManyToManyField(ModelObject, related_name='changelog_previous')
    currently = models.ManyToManyField(ModelObject, related_name='changelog_current')

    def __str__(self):
        return '{2}\n{0}\n\tchanged to\n{1}; '.format("\n".join(str(v) for v in self.previously.all()),
                                              "\n".join(str(v) for v in self.currently.all()), self.updated_at)


class ModelChangelog(BaseModel):
    """General changelog, saves which fields are removede, inserted (both m2m) and which are modified."""

    modification = models.OneToOneField(ModelModification, null=True, on_delete=models.CASCADE)
    inserted = models.ManyToManyField(ModelObject, related_name='changelog_inserted')
    removed = models.ManyToManyField(ModelObject, related_name='changelog_removed')

    information = models.OneToOneField(ModelObject, null=True, on_delete=models.CASCADE)

    def __str__(self):
        output = 'Time: {0},\nItem: {1}'.format(self.updated_at, self.information)
        if self.modification is not None:
            output += '\nModification at {0}:\n\t{1}\n\t\tchanged to\n\t{2};\n'.format(
                self.modification.updated_at,
                "\n\t".join(str(v) for v in self.modification.previously.all()),
                "\n\t".join(str(v) for v in self.modification.currently.all()))
        if self.inserted.count() > 0:
            output += 'Insert at {0}:\n\t{1}'.format(
                self.modification.updated_at,
                "\n\t".join(str(v) for v in self.inserted.all())
            )
        if self.removed.count() > 0:
            output += 'Delete at {0}:\n\t{1}'.format(
                self.modification.updated_at,
                "\n\t".join(str(v) for v in self.removed.all())
            )

        return output


class Model(BaseModel):
    """This ties a changelog to a specific user, this is used by the DatabaseHandler."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='atl_model_application', null=True)

    message = models.TextField(null=True)

    MODES = (
        (0, 'n/a'),
        (1, 'add'),
        (2, 'change'),
        (3, 'delete'),
    )
    action = models.PositiveSmallIntegerField(choices=MODES, default=0)

    information = models.OneToOneField(ModelObject, on_delete=models.CASCADE, related_name='atl_model_information', null=True)
    modification = models.ForeignKey(ModelChangelog, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return 'Time: {0}, User: {1}, Action: {2}, App: {3},\nModification: {5}'.format(
            self.created_at,
            self.user,
            self.MODES[self.action][1],
            self.application,
            self.information,
            self.modification
        )

    class Meta:
        verbose_name = 'Changelog'
        verbose_name_plural = 'Changelogs'


class Request(BaseModel):
    """The model where every request is saved."""

    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True)

    uri = models.URLField()
    method = models.CharField(max_length=64)
    status = models.PositiveSmallIntegerField(null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return '{2} - {0} performed request at {3} ({1})'.format(self.user, self.created_at, self.uri, self.application)

    class Meta:
        verbose_name = "Request"
        verbose_name_plural = "Requests"


class Unspecified(BaseModel):
    """Logging messages that are saved by non DAL systems."""

    message = models.TextField(null=True)
    level = models.PositiveSmallIntegerField(default=20)

    file = models.CharField(max_length=255, null=True)
    line = models.PositiveIntegerField(null=True)

    def __str__(self):
        if self.level == 10:
            level = 'DEBUG'
        elif self.level == 20:
            level = 'INFO'
        elif self.level == 30:
            level = 'WARNING'
        elif self.level == 40:
            level = 'ERROR'
        elif self.level == 50:
            level = 'CRITICAL'
        else:
            level = 'NOTSET'

        return '{} - {} - {} ({} - {})'.format(self.created_at, level, self.message, self.file, self.line)

    class Meta:
        verbose_name = "Non DAL Message"
        verbose_name_plural = "Non DAL Messages"


from core.models import User


class LogModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    source_url = models.TextField(max_length=1000)
    time = models.DateTimeField(auto_now=True)

    MODES = (
        (0, 'other'),
        (1, 'move'),
        (2, 'login'),
        (3, 'logout'),
        (4, 'search')
    )
    action = models.PositiveSmallIntegerField(choices=MODES, default=0)
    args = models.TextField(max_length=2000)

    def __str__(self):
        return "Time: {0}, User: {1}, Action: {2}, URL: {3}, Args: {4}".format(
            self.time,
            self.user,
            self.MODES[self.action][1],
            self.source_url,
            self.args
        )
