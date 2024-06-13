from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()
    
class DateRangeForm(forms.Form):
    start_date = forms.DateField(label="Fecha de inicio", widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label="Fecha de fin", widget=forms.DateInput(attrs={'type': 'date'}))