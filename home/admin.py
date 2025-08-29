from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(AbsenceData)
admin.site.register(EmployeeData)
admin.site.register(PracticeData)