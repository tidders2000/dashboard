import csv
from io import TextIOWrapper
from datetime import datetime
from django.shortcuts import render, redirect
from .models import AbsenceData,EmployeeData
from django.contrib.auth.decorators import login_required
from django.db.models import Sum,Count
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.core import serializers
from .forms import filterForm
from datetime import date,datetime,timedelta
from django.db.models import Sum, Count, Q, Max
from django.contrib import messages
import io
from django.utils import timezone


@login_required

def home(request):
    
    user = request.user.profile
    practice = user.practice
    absence_percent=0
   #gets dates back from user to filter content
    form = filterForm()
    if request.method=='POST':
        form = filterForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            #now in the object cd, you have the form as a dictionary.
            start = cd.get('start')
            end = cd.get('end')
            st = start
            en = end
            delta = en - st  # timedelta
            weeks = round(delta.days / 7) #works out weeks in user stated period
                 
                 
              
          
            request.session['start_date'] = form.cleaned_data['start'].isoformat()
            request.session['end_date'] = form.cleaned_data['end'].isoformat()
           
        
            # request.session['start'] = start
            # request.session['end'] = end
            



    else: 
       
        tod='2025/04/01'
        en= date.today()   

        st = datetime.strptime(tod, '%Y/%m/%d').date()            
        delta= en - st
        weeks = round(delta.days / 7)
        request.session['end_date'] = date.today().isoformat()  
        request.session['start_date'] = st.isoformat()
 
#headcount by department  
    leavers = (
        EmployeeData.objects
        .filter(leaving_date__gte=st, leaving_date__lte=en,practice=practice)
        .values('Department')
        .annotate(leaver_count=Count('id'))
    )

    # Step 2: Get current headcount (people still in post as of end_date)
    headcounts = (
        EmployeeData.objects
        .filter(Q(leaving_date__isnull=True) | Q(leaving_date__gte=en),practice=practice)
        .values('Department')
        .annotate(headcount=Count('id'))
    )

    # Step 3: Build dictionary for quick lookup
    headcount_dict = {item['Department']: item['headcount'] for item in headcounts}

    # Step 4: Combine leavers and headcount, calculate turnover
    hcresults = []
    for item in leavers:
        dept = item['Department']
        leaver_count = item['leaver_count']
        headcount = headcount_dict.get(dept, 0)
        turnover_rate = round((leaver_count / headcount) * 100, 2) if headcount else 0

        hcresults.append({
            'department': dept,
            'leavers': leaver_count,
            'headcount': headcount,
            'turnover_rate': turnover_rate,
        })
    
    # identify user          
    user=request.user.profile
    # identify practice
    practice=user.practice
    #total days by 
    # tot_days=AbsenceData.objects.filter(practice=practice,start__range=[st, en]).annotate(count=Sum('days'))
    # dept__in=
    #headcount by practice sum total
    headcount_prime = EmployeeData.objects.filter(practice__iexact=practice, leaving_date__isnull=True).count()
 
 
   

    #hours by total for practice
    weekly_hours =EmployeeData.objects.filter(practice=practice,leaving_date__isnull=True).aggregate(total=Sum('hours'))

    #leavers by practice
    leavers = EmployeeData.objects.filter(practice=practice,leaving_date__isnull=False, leaving_date__gte=st)
    #starters by practice

   
    starters = EmployeeData.objects.filter(
    practice=practice,
    leaving_date__isnull=True,
    start_date__gte=st
)
    #fte 
    fte=  round(weekly_hours['total']/37.5,2)

    #gets absence days by dept

    absence_summary = (
        AbsenceData.objects
        .filter(start__gte=st, end__lte=en,practice=practice)
        .values('department')
        .annotate(total_days=Sum('days'))
    )

    # Headcount per department (excluding people with a leaving_date before end_date)
    headcounts = (
        EmployeeData.objects
        .filter(Q(leaving_date__isnull=True) | Q(leaving_date__gte=en),practice=practice)
        .values('Department')
        .annotate(headcount=Count('id'))
    )

    # Convert headcounts to a dictionary for lookup
    headcount_dict = {item['Department']: item['headcount'] for item in headcounts}

    # Merge absence and headcount data
    result = []
    for item in absence_summary:
        dept = item['department']
        total_days = item['total_days']
        headcount = headcount_dict.get(dept, 0)
        avg_days = round(total_days / headcount, 2) if headcount else 0

        result.append({
            'department': dept,
            'total_days': total_days,
            'headcount': headcount,
            'average_days': avg_days,
        })

    td=AbsenceData.objects.aggregate(days_total=Sum("days", default=0),)
    ap=round(1000/(td['days_total']*7),2)
    #calculate staff turnover by practice
    leavers_count=EmployeeData.objects.filter(leaving_date__isnull=False,practice=practice).count()
 

    turnover_prime=round(leavers_count/headcount_prime*100,2)


    #if user inputs date period
    if weeks:
        
        #calculate absence %
        #work out total weekly hours multipled by weeks in period
        total_hours_period=round(weekly_hours['total']*weeks)
   
        #work out amount of days sick in selected period
        sick_days = AbsenceData.objects.filter(start__range=[st, en],practice=practice).aggregate(days_total=Sum("days", default=0),)
        #work out sick hours total for period
        total_sick_hours_period= (sick_days['days_total']*7.5)

        average_sick_person=round(sick_days['days_total']/headcount_prime,2)
      
        #work out %
        absence_percent= round(total_sick_hours_period/total_hours_period*100,2)
        
        leavers = EmployeeData.objects.filter(practice=practice,leaving_date__isnull=False)
    
    context = {
        'absence_percent':absence_percent,
        'form':form,
        'headcount':headcount_prime,
        'weekly_hours':weekly_hours,
        'leavers':leavers,
        'starters':starters,
        'fte':fte,
        'turnover':turnover_prime,
        'average_sick_person':average_sick_person,
        'absence_data':result,
        'turnover_data':hcresults
    }
            
   
    return render(request,'index.html',context)


def gender(request):
        # identify user          
    user=request.user.profile
    # identify practice
    practice=user.practice
    gender_data = (
        EmployeeData.objects
        .filter(practice=practice)
        .values('gender')
        .annotate(count=Count('id'))
    )

    labels = [item['gender'] for item in gender_data]
    data = [item['count'] for item in gender_data]

    return JsonResponse({'labels': labels, 'data': data})

def employee_age_chart_data(request):
    # Define your age ranges
    age_ranges = {
        '20–29': (20, 29),
        '30–39': (30, 39),
        '40–49': (40, 49),
        '50–59': (50, 59),
        '60–69': (60, 69),
        '70+': (70, 200),  # Upper bound high to catch any older ages
    }
        # identify user          
    user=request.user.profile
    # identify practice
    practice=user.practice

    # Initialize counters
    age_group_counts = {label: 0 for label in age_ranges}

    # Group employees by age range
    for employee in EmployeeData.objects.filter(practice=practice,leaving_date__isnull=True):
        for label, (min_age, max_age) in age_ranges.items():
            if min_age <= employee.age <= max_age:
                age_group_counts[label] += 1
                break

    # Prepare JSON response
    response_data = {
        'labels': list(age_group_counts.keys()),
        'data': list(age_group_counts.values()),
    }

    return JsonResponse(response_data)


def upload_csv(request):
    latest_start = AbsenceData.objects.aggregate(latest=Max('start'))['latest']
    if request.method == 'POST' and request.FILES.get('csv_file'):
        file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
        reader = csv.DictReader(file)  # uses headers: start, end, reason, days, practice
        reader.fieldnames = [field.strip().lower().replace('\ufeff', '') for field in reader.fieldnames]

        for row in reader:
            print("CSV row keys:", row.keys())
            AbsenceData.objects.create(
                start=datetime.strptime(row['start'], '%d/%m/%Y').date(),
                end=datetime.strptime(row['end'], '%d/%m/%Y').date(),
                reason=row['reason'],
                days=float(row['days']),
                practice=row['practice'],
                department=row['department'],
                uploaded_by=request.user
)
        return redirect('index.html')  # or any other page
    return render(request, 'upload.html',{'latest_start':latest_start})

#workforce upload
def upload_workforce(request):

            # identify user          
    user=request.user.profile
    # identify practice
    practice=user.practice
    EmployeeData.objects.filter(practice=practice).delete()
 
    if request.method == 'POST' and request.FILES.get('csv_file'):
        user=request.user.profile
    # identify practice
        practice=user.practice
        EmployeeData.objects.filter(practice=practice).delete()
        file = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
        reader = csv.DictReader(file)  # uses headers: start, end, reason, days, practice
        reader.fieldnames = [field.strip().lower().replace('\ufeff', '') for field in reader.fieldnames]
        for row in reader:
            print("CSV row keys:", row.keys())
            
            leaving_date = None
            if row['leaving_date'].strip():  # only parse if not blank
                leaving_date = datetime.strptime(row['leaving_date'], '%d/%m/%Y').date()

            EmployeeData.objects.create(
                practice=row['practice'],
                Department=row['department'],
                hours=float(row['hours']),
                gender=row['gender'],
                race=row['race'],
                pay=float(row['pay']),
                age=float(row['age']),
                status=row['status'],
                start_date=datetime.strptime(row['start_date'], '%d/%m/%Y').date(),
                leaving_date=leaving_date,  # will be None if blank
            )


        return redirect('home')  # or any other page
    return render(request, 'upload')
#leavers upload
def upload_leavers_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        file = request.FILES['csv_file']
        
        if not file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect('home')

        data_set = file.read().decode('utf-8-sig')
        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string)

        updated = 0
        not_found = 0

        for row in reader:
            try:
                hours = int(row['hours'])
                start_date = datetime.strptime(row['start_date'], '%d/%m/%Y').date()
                leaving_date = datetime.strptime(row['leaving_date'], '%d/%m/%Y').date()

                department = row['department']

                # Try to find the matching record
                employee = EmployeeData.objects.filter(
                    hours=hours,
                    start_date=start_date,
                    Department__iexact=department
                ).first()

                if employee:
                    employee.leaving_date = leaving_date
                    employee.save()
                    updated += 1
                else:
                    not_found += 1

            except Exception as e:
                messages.error(request, f'Error processing row: {row} — {e}')
        
        messages.success(request, f'Updated {updated} records. {not_found} not matched.')

        return redirect('home')  # Replace with your actual redirect

    return render(request, 'upload')  # Replace with your actual template
#absence data endpoint
def absence_chart(request):
   
    user = request.user.profile
    practice = user.practice
    
    start = request.session.get('start_date')
    end = request.session.get('end_date')


    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()


    absence_summary = (

        AbsenceData.objects
        .filter(practice=practice,start__range=[start_date, end_date] )
        .values('reason')
        .annotate(total_days=Sum('days'))
    )

    # Convert to lists for Chart.js
    labels = [item['reason'] for item in absence_summary]
    values = [item['total_days'] for item in absence_summary]

    return JsonResponse({
        "title": "Absence",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "Days Absent",
                "data": values,
             
            }]
        }
    })
# headcount endpoint
def headcount(request):
    user = request.user.profile
    practice = user.practice
    headcount_summary = (
        EmployeeData.objects
        .filter(practice=practice,leaving_date__isnull=True)
        .values('Department')
        .annotate(total_dep=Count('Department'))
    )

    labels = [item['Department'] for item in headcount_summary]
    values = [item['total_dep'] for item in headcount_summary]

    
    return JsonResponse({
        "title": "Headcount Breakdown",
        "data": {
            "labels": labels,
            "datasets": [{
               
                "data": values,
                "label": "Number of Employees",
             
            }]
        }
    })
# race chart endpoint
def race(request):
    user = request.user.profile
    practice = user.practice
    headcount_summary = (
        EmployeeData.objects
        .filter(practice=practice,leaving_date__isnull=True)
        .values('race')
        .annotate(total_race=Count('race'))
    )

    labels = [item['race'] for item in headcount_summary]
    values = [item['total_race'] for item in headcount_summary]

    
    return JsonResponse({
        "title": "Headcount Breakdown",
        "data": {
            "labels": labels,
            "datasets": [{
               
                "data": values,
                    "label": "Number of Employees",
             
            }]
        }
    })
# absence chart
def chart_data(request):
    

    # Get all distinct reasons
    user=request.user.profile
    practice=user.practice
    

    # get absence data by practice
    
    reasons = AbsenceData.objects.values_list('reason', flat=True).distinct()

    # Get all distinct practices
    practices = AbsenceData.objects.values_list('practice', flat=True).filter(practice=practice)

    # Prepare dataset structure for Chart.js
    datasets = []
    for reason in reasons:
        data = []
        for practice in practices:
            total = AbsenceData.objects.filter(
                reason=reason,
                practice=practice
               
            ).aggregate(Sum('days'))['days__sum'] or 0
            data.append(total)
        datasets.append({
            'label': reason,
            'data': data,
        })

    return JsonResponse({
        'labels': list(practices),  # X-axis labels
        'datasets': datasets        # one dataset per reason
    })


@login_required

def global_dash(request):

    tod='2025/04/01'
    en= date.today()   

    st = datetime.strptime(tod, '%Y/%m/%d').date()            
    delta= en - st
    weeks = round(delta.days / 7)


    #headcount by practice sum total
    headcount_prime = EmployeeData.objects.filter(leaving_date__isnull=True).count()
 
 

    #hours by total for practice
    weekly_hours =EmployeeData.objects.filter(leaving_date__isnull=True).aggregate(total=Sum('hours'))
 
    #leavers by practice
    leavers = EmployeeData.objects.filter(leaving_date__isnull=False)
    #starters by practice
    starters = EmployeeData.objects.filter(leaving_date__isnull=True)
    #fte 
    fte=  round(weekly_hours['total']/37.5,2)

    leavers_count=EmployeeData.objects.filter(leaving_date__isnull=True).count()
 
   

    total_hours_period=round(weekly_hours['total']/7.5*weeks)
        #work out amount of days sick in selected period
    sick_days = AbsenceData.objects.filter(start__range=[st, en]).aggregate(days_total=Sum("days", default=0),)
        #work out sick hours total for period
    total_sick_hours_period= (sick_days['days_total']*7.5)
        #work out %
    absence_percent= round(total_sick_hours_period/total_hours_period,2)

    absence_summary = (
        AbsenceData.objects
        .filter(start__gte=st, end__lte=en)
        .values('department')
        .annotate(total_days=Sum('days'))
    )

    headcounts = (
        EmployeeData.objects
        .filter(Q(leaving_date__isnull=True) | Q(leaving_date__gte=en))
        .values('Department')
        .annotate(headcount=Count('id'))
    )

    # Convert headcounts to a dictionary for lookup
    headcount_dict = {item['Department']: item['headcount'] for item in headcounts}

    # Merge absence and headcount data
    result = []
    for item in absence_summary:
        dept = item['department']
        total_days = item['total_days']
        headcount = headcount_dict.get(dept, 0)
        avg_days = round(total_days / headcount, 2) if headcount else 0

        result.append({
            'department': dept,
            'total_days': total_days,
            'headcount': headcount,
            'average_days': avg_days,
        })
    leavers_count=EmployeeData.objects.filter(leaving_date__isnull=False).count()
    turnover_prime=round(leavers_count/headcount_prime*100,2)
  
    leavers_tot = (
        EmployeeData.objects
        .filter(leaving_date__gte=st, leaving_date__lte=en)
        .values('Department')
        .annotate(leaver_count=Count('id'))
    )

    hcresults = []
    for item in leavers_tot:
        dept = item['Department']
        leaver_count = item['leaver_count']
        headcount = headcount_dict.get(dept, 0)
        turnover_rate = round((leaver_count / headcount) * 100, 2) if headcount else 0

        hcresults.append({
            'department': dept,
            'leavers': leaver_count,
            'headcount': headcount,
            'turnover_rate': turnover_rate,
        })


      
    context = {
        'absence_percent':absence_percent,
        
        'headcount':headcount_prime,
        'weekly_hours':weekly_hours,
        'leavers':leavers,
        'starters':starters,
        'fte':fte,
        'turnover':turnover_prime,
       
        'absence_data':result,
        'turnover_data':hcresults
    }
       
    return render(request,'globaldash.html',context)

def headcount_global(request):
   
    headcount_summary = (
        EmployeeData.objects
        .filter(leaving_date__isnull=True)
        .values('Department')
        .annotate(total_dep=Count('Department'))
    )

    labels = [item['Department'] for item in headcount_summary]
    values = [item['total_dep'] for item in headcount_summary]

    
    return JsonResponse({
        "title": "Headcount Breakdown",
        "data": {
            "labels": labels,
            "datasets": [{
               
                "data": values,
                "label": "Number of Employees",
             
            }]
        }
    })

def race_global(request):
    user = request.user.profile
    practice = user.practice
    headcount_summary = (
        EmployeeData.objects
        .filter(leaving_date__isnull=True)
        .values('race')
        .annotate(total_race=Count('race'))
    )

    labels = [item['race'] for item in headcount_summary]
    values = [item['total_race'] for item in headcount_summary]

    
    return JsonResponse({
        "title": "Headcount Breakdown",
        "data": {
            "labels": labels,
            "datasets": [{
               
                "data": values,
                    "label": "Number of Employees",
             
            }]
        }
    })

def employee_age_chart_data_global(request):
    # Define your age ranges
    age_ranges = {
        '20–29': (20, 29),
        '30–39': (30, 39),
        '40–49': (40, 49),
        '50–59': (50, 59),
        '60–69': (60, 69),
        '70+': (70, 200),  # Upper bound high to catch any older ages
    }
        # identify user          


    # Initialize counters
    age_group_counts = {label: 0 for label in age_ranges}

    # Group employees by age range
    for employee in EmployeeData.objects.filter(leaving_date__isnull=True):
        for label, (min_age, max_age) in age_ranges.items():
            if min_age <= employee.age <= max_age:
                age_group_counts[label] += 1
                break

    # Prepare JSON response
    response_data = {
        'labels': list(age_group_counts.keys()),
        'data': list(age_group_counts.values()),
    }

    return JsonResponse(response_data)

def absence_chart_global(request):
   
    user = request.user.profile

    
    start = request.session.get('start_date')
    end = request.session.get('end_date')


    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()


    absence_summary = (

        AbsenceData.objects
        .filter(start__range=[start_date, end_date] )
        .values('reason')
        .annotate(total_days=Sum('days'))
    )

    # Convert to lists for Chart.js
    labels = [item['reason'] for item in absence_summary]
    values = [item['total_days'] for item in absence_summary]

    return JsonResponse({
        "title": "Absence",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "Days Absent",
                "data": values,
             
            }]
        }
    })