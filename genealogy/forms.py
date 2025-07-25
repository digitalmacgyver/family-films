from django import forms
from django.core.exceptions import ValidationError
from main.models import Person


class PersonRelationshipForm(forms.ModelForm):
    """Form for editing person relationships"""
    
    class Meta:
        model = Person
        fields = ['father', 'mother', 'spouse']
        widgets = {
            'father': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Select father...'
            }),
            'mother': forms.Select(attrs={
                'class': 'form-control', 
                'data-placeholder': 'Select mother...'
            }),
            'spouse': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Select spouse...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add empty choice
        empty_choice = [('', '--- None ---')]
        
        # Exclude self from relationship choices
        if self.instance and self.instance.pk:
            queryset = Person.objects.exclude(pk=self.instance.pk).order_by('last_name', 'first_name')
            
            # Set querysets with empty choice
            self.fields['father'].queryset = queryset
            self.fields['father'].choices = empty_choice + [(p.pk, p.full_name_reversed()) for p in queryset]
            
            self.fields['mother'].queryset = queryset  
            self.fields['mother'].choices = empty_choice + [(p.pk, p.full_name_reversed()) for p in queryset]
            
            self.fields['spouse'].queryset = queryset
            self.fields['spouse'].choices = empty_choice + [(p.pk, p.full_name_reversed()) for p in queryset]
        else:
            # For new instances, show all people
            queryset = Person.objects.all().order_by('last_name', 'first_name')
            
            self.fields['father'].queryset = queryset
            self.fields['father'].choices = empty_choice + [(p.pk, p.full_name_reversed()) for p in queryset]
            
            self.fields['mother'].queryset = queryset
            self.fields['mother'].choices = empty_choice + [(p.pk, p.full_name_reversed()) for p in queryset]
            
            self.fields['spouse'].queryset = queryset
            self.fields['spouse'].choices = empty_choice + [(p.pk, p.full_name_reversed()) for p in queryset]
    
    def clean(self):
        cleaned_data = super().clean()
        father = cleaned_data.get('father')
        mother = cleaned_data.get('mother')
        spouse = cleaned_data.get('spouse')
        
        # Prevent self-reference (additional check)
        if self.instance and self.instance.pk:
            if father and father.pk == self.instance.pk:
                raise ValidationError("Person cannot be their own father")
            if mother and mother.pk == self.instance.pk:
                raise ValidationError("Person cannot be their own mother")
            if spouse and spouse.pk == self.instance.pk:
                raise ValidationError("Person cannot be their own spouse")
        
        return cleaned_data


class PersonBiographyForm(forms.ModelForm):
    """Form for editing person biography"""
    
    class Meta:
        model = Person
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': 'Enter biographical information, life events, memories, and other personal details...'
            })
        }
        labels = {
            'notes': 'Biography & Notes'
        }
        help_texts = {
            'notes': 'Share stories, memories, and important life events for this person.'
        }


class PersonBasicInfoForm(forms.ModelForm):
    """Form for editing basic person information"""
    
    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'birth_date', 'death_date']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'death_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        help_texts = {
            'birth_date': 'Leave empty if unknown',
            'death_date': 'Leave empty if person is still living'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        birth_date = cleaned_data.get('birth_date')
        death_date = cleaned_data.get('death_date')
        
        # Validate date order
        if birth_date and death_date:
            if death_date <= birth_date:
                raise ValidationError("Death date must be after birth date")
        
        return cleaned_data