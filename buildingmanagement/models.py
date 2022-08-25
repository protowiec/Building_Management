from django.db import models
from django.db import transaction
from django.db.models import F, Q
from django.db.models import UniqueConstraint, CheckConstraint
from django.conf import settings


class Room(models.Model):
    name = models.CharField(max_length=100)
    people_count = models.PositiveSmallIntegerField(default=0)
    max_people_count = models.PositiveSmallIntegerField(null=False)
    image = models.ImageField(upload_to="images/", null=True)

    class Meta:
        constraints = [
            CheckConstraint(
                check=Q(people_count__lte=F('max_people_count')),
                name="people_count_maximum"
            )
        ]

    def __str__(self):
        return self.name

    @transaction.atomic
    def move_people_to(self, other_room, count=1):

        # inne podejscie do radzenia sobie z równoległymi zapisami do bazy (blokuje do końca transakcji)
        Room.objects.filter(id=self.id).select_for_update()
        Room.objects.filter(id=other_room.id).select_for_update()
        self.people_count -= count
        self.save()
        other_room.people_count += count
        other_room.save()

    def get_reserved_days(self, month):
        return Reservation.objects.filter(room=self).\
            filter(date__month=month).values_list("date__day", flat=True)


class Reservation(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    date = models.DateField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=["room", "date"], name="unique_room_reservation")
        ]
        ordering = ['date']

    def __str__(self):
        return f"{self.room.name}/{self.date}"


class Projector(models.Model):
    producer = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    room = models.OneToOneField(Room, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.producer}/{self.serial_number}"


class AccessCard(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    rooms = models.ManyToManyField(Room, related_name="accesscards")

    def __str__(self):
        return f"{self.owner.username.capitalize()}'s card ({self.id})"


class UserProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    position = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user} profile"
