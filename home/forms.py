from django import forms

class filterForm(forms.Form):

    start=forms.DateField()
    end=forms.DateField()
    

