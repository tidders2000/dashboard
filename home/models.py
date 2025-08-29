from django.db import models
from django.contrib.auth.models import User
from datetime import date
# Create your models here.
# models.py

class AbsenceData(models.Model):  # <-- NOT AbsenceData
    start = models.DateField()
    end = models.DateField()
    reason = models.CharField(max_length=255)
    days = models.IntegerField()
    practice = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

class EmployeeData(models.Model):
    practice = models.CharField(max_length=255)
    Department = models.CharField(max_length=255)
    pay = models.DecimalField(max_digits=4, decimal_places=2)
    hours = models.IntegerField()
    gender = models.CharField(max_length=255)
    race = models.CharField(max_length=255)
    age=models.IntegerField()
    status=models.CharField()
    start_date=models.DateField()
    leaving_date=models.DateField(blank=True, null=True )


class PracticeData(models.Model):
     practice = models.CharField(max_length=255)
     headcount = models.IntegerField()
     fulltime_hours=models.IntegerField()

