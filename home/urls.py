from django.contrib import admin
from django.urls import path, include
from .views import *
from users import views as users_views

urlpatterns = [
path('', home, name='home'),
path('upload/',upload_csv,name='upload'),
path('headcount/',headcount,name='headcount'),
path('race/',race,name='race'),
path('chart_data/',chart_data,name='chart_data'),
path("absence_chart/", absence_chart, name="absence_chart"),
path("age_data/", employee_age_chart_data, name="age"),
path('workforce',upload_workforce,name='workforce'),
path('leavers/',upload_leavers_csv,name='leavers'),
path('profile/',users_views.profilepage,name='profile'),
path('globaldash/',global_dash,name='globaldash'),
path('gender/',gender,name='gender'),
path('headcount_global/',headcount_global,name='headcount_global'),
path('race_global/',race_global,name='race_global'),
path("age_data_global/", employee_age_chart_data_global, name="age_global"),
path("absence_chart_global/", absence_chart_global, name="absence_chart_global"),


]