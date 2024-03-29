from __future__ import unicode_literals, absolute_import

from django.db import models
from django.db.models import Manager
from six import python_2_unicode_compatible
from django.utils.translation import gettext_lazy as _

from model_utils import Choices
from model_utils.fields import SplitField, MonitorField, StatusField
from model_utils.managers import QueryManager, InheritanceManager
from model_utils.models import (
    SoftDeletableModel,
    StatusModel,
    TimeFramedModel,
    TimeStampedModel,
)
from tests.fields import MutableField
from tests.managers import CustomSoftDeleteManager
from model_utils.tracker import FieldTracker, ModelTracker


class InheritanceManagerTestRelated(models.Model):
    pass


@python_2_unicode_compatible
class InheritanceManagerTestParent(models.Model):
    # FileField is just a handy descriptor-using field. Refs #6.
    non_related_field_using_descriptor = models.FileField(upload_to="test")
    related = models.ForeignKey(
        InheritanceManagerTestRelated, related_name="imtests", null=True,
        on_delete=models.CASCADE)
    normal_field = models.TextField()
    related_self = models.OneToOneField(
        "self", related_name="imtests_self", null=True,
        on_delete=models.CASCADE)
    objects = InheritanceManager()

    def __unicode__(self):
        return unicode(self.pk)

    def __str__(self):
        return "%s(%s)" % (
            self.__class__.__name__[len('InheritanceManagerTest'):],
            self.pk,
        )


class InheritanceManagerTestChild1(InheritanceManagerTestParent):
    non_related_field_using_descriptor_2 = models.FileField(upload_to="test")
    normal_field_2 = models.TextField()
    objects = InheritanceManager()


class InheritanceManagerTestGrandChild1(InheritanceManagerTestChild1):
    text_field = models.TextField()


class InheritanceManagerTestGrandChild1_2(InheritanceManagerTestChild1):
    text_field = models.TextField()


class InheritanceManagerTestChild2(InheritanceManagerTestParent):
    non_related_field_using_descriptor_2 = models.FileField(upload_to="test")
    normal_field_2 = models.TextField()


class InheritanceManagerTestChild3(InheritanceManagerTestParent):
    parent_ptr = models.OneToOneField(
        InheritanceManagerTestParent, related_name='manual_onetoone',
        parent_link=True, on_delete=models.CASCADE)


class TimeStamp(TimeStampedModel):
    pass


class TimeFrame(TimeFramedModel):
    pass


class TimeFrameManagerAdded(TimeFramedModel):
    pass


class Monitored(models.Model):
    name = models.CharField(max_length=25)
    name_changed = MonitorField(monitor="name")


class MonitorWhen(models.Model):
    name = models.CharField(max_length=25)
    name_changed = MonitorField(monitor="name", when=["Jose", "Maria"])


class MonitorWhenEmpty(models.Model):
    name = models.CharField(max_length=25)
    name_changed = MonitorField(monitor="name", when=[])


class DoubleMonitored(models.Model):
    name = models.CharField(max_length=25)
    name_changed = MonitorField(monitor="name")
    name2 = models.CharField(max_length=25)
    name_changed2 = MonitorField(monitor="name2")


class Status(StatusModel):
    STATUS = Choices(
        ("active", _("active")),
        ("deleted", _("deleted")),
        ("on_hold", _("on hold")),
    )


class StatusPlainTuple(StatusModel):
    STATUS = (
        ("active", _("active")),
        ("deleted", _("deleted")),
        ("on_hold", _("on hold")),
    )


class StatusManagerAdded(StatusModel):
    STATUS = (
        ("active", _("active")),
        ("deleted", _("deleted")),
        ("on_hold", _("on hold")),
    )


class StatusCustomManager(Manager):
    pass


class AbstractStatusCustomManager(StatusModel):
    STATUS = Choices(
        ("first_choice", _("First choice")),
        ("second_choice", _("Second choice")),
    )

    objects = StatusCustomManager()

    class Meta:
        abstract = True


class StatusCustomManager(AbstractStatusCustomManager):
    title = models.CharField(max_length=50)


class Post(models.Model):
    published = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)
    order = models.IntegerField()

    objects = models.Manager()
    public = QueryManager(published=True)
    public_confirmed = QueryManager(models.Q(published=True) &
                                    models.Q(confirmed=True))
    public_reversed = QueryManager(published=True).order_by("-order")

    class Meta:
        ordering = ("order",)


class Article(models.Model):
    title = models.CharField(max_length=50)
    body = SplitField()


class SplitFieldAbstractParent(models.Model):
    content = SplitField()

    class Meta:
        abstract = True


class NoRendered(models.Model):
    """
    Test that the no_excerpt_field keyword arg works. This arg should
    never be used except by the South model-freezing.

    """
    body = SplitField(no_excerpt_field=True)


class AuthorMixin(object):
    def by_author(self, name):
        return self.filter(author=name)


class PublishedMixin(object):
    def published(self):
        return self.filter(published=True)


def unpublished(self):
    return self.filter(published=False)


class ByAuthorQuerySet(models.query.QuerySet, AuthorMixin):
    pass


class FeaturedManager(models.Manager):
    def get_queryset(self):
        kwargs = {}
        if hasattr(self, "_db"):
            kwargs["using"] = self._db
        return ByAuthorQuerySet(self.model, **kwargs).filter(feature=True)


class Tracked(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()
    mutable = MutableField(default=None)

    tracker = FieldTracker()


class TrackedFK(models.Model):
    fk = models.ForeignKey('Tracked', on_delete=models.CASCADE)

    tracker = FieldTracker()
    custom_tracker = FieldTracker(fields=['fk_id'])
    custom_tracker_without_id = FieldTracker(fields=['fk'])


class TrackedNotDefault(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    name_tracker = FieldTracker(fields=['name'])


class TrackedNonFieldAttr(models.Model):
    number = models.FloatField()

    @property
    def rounded(self):
        return round(self.number) if self.number is not None else None

    tracker = FieldTracker(fields=['rounded'])


class TrackedMultiple(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    name_tracker = FieldTracker(fields=['name'])
    number_tracker = FieldTracker(fields=['number'])


class TrackedFileField(models.Model):
    some_file = models.FileField(upload_to='test_location')

    tracker = FieldTracker()


class InheritedTracked(Tracked):
    name2 = models.CharField(max_length=20)


class InheritedTrackedFK(TrackedFK):
    custom_tracker = FieldTracker(fields=['fk_id'])
    custom_tracker_without_id = FieldTracker(fields=['fk'])


class ModelTracked(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()
    mutable = MutableField(default=None)

    tracker = ModelTracker()


class ModelTrackedFK(models.Model):
    fk = models.ForeignKey('ModelTracked', on_delete=models.CASCADE)

    tracker = ModelTracker()
    custom_tracker = ModelTracker(fields=['fk_id'])
    custom_tracker_without_id = ModelTracker(fields=['fk'])


class ModelTrackedNotDefault(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    name_tracker = ModelTracker(fields=['name'])


class ModelTrackedMultiple(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    name_tracker = ModelTracker(fields=['name'])
    number_tracker = ModelTracker(fields=['number'])


class InheritedModelTracked(ModelTracked):
    name2 = models.CharField(max_length=20)


class StatusFieldDefaultFilled(models.Model):
    STATUS = Choices((0, "no", "No"), (1, "yes", "Yes"))
    status = StatusField(default=STATUS.yes)


class StatusFieldDefaultNotFilled(models.Model):
    STATUS = Choices((0, "no", "No"), (1, "yes", "Yes"))
    status = StatusField()


class StatusFieldChoicesName(models.Model):
    NAMED_STATUS = Choices((0, "no", "No"), (1, "yes", "Yes"))
    status = StatusField(choices_name='NAMED_STATUS')


class SoftDeletable(SoftDeletableModel):
    """
    Test model with additional manager for full access to model
    instances.
    """
    name = models.CharField(max_length=20)

    all_objects = models.Manager()


class CustomSoftDelete(SoftDeletableModel):
    is_read = models.BooleanField(default=False)

    objects = CustomSoftDeleteManager()
