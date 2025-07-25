from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.db import models
from main.models import Person
from .forms import PersonRelationshipForm, PersonBiographyForm


class GenealogyHomeView(TemplateView):
    """Main genealogy landing page"""
    template_name = 'genealogy/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get some featured people for the home page
        context['featured_people'] = Person.objects.filter(
            models.Q(father__isnull=False) | 
            models.Q(mother__isnull=False) | 
            models.Q(spouse__isnull=False)
        ).distinct()[:10]
        return context


class FamilyTreeView(DetailView):
    """Interactive family tree centered on a person"""
    model = Person
    template_name = 'genealogy/tree.html'
    context_object_name = 'person'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add tree data for initial load
        context['tree_data'] = self.object.get_family_tree_data()
        return context


class PersonRelationshipEditView(LoginRequiredMixin, UpdateView):
    """Edit person's family relationships"""
    model = Person
    form_class = PersonRelationshipForm
    template_name = 'genealogy/person_edit.html'
    
    def get_success_url(self):
        messages.success(self.request, f'Relationships updated for {self.object.full_name()}')
        return reverse_lazy('genealogy:tree', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Run model validation
        try:
            form.instance.full_clean()
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        return super().form_valid(form)


class PersonBiographyView(DetailView):
    """Display person biography"""
    model = Person
    template_name = 'genealogy/person_bio.html'
    context_object_name = 'person'


class PersonBiographyEditView(LoginRequiredMixin, UpdateView):
    """Edit person biography"""
    model = Person
    form_class = PersonBiographyForm
    template_name = 'genealogy/person_bio_edit.html'
    
    def get_success_url(self):
        messages.success(self.request, f'Biography updated for {self.object.full_name()}')
        return reverse_lazy('genealogy:biography', kwargs={'pk': self.object.pk})


# API Views
class FamilyTreeAPIView(DetailView):
    """JSON API for family tree data"""
    model = Person
    
    def get(self, request, *args, **kwargs):
        person = self.get_object()
        tree_data = person.get_family_tree_data()
        return JsonResponse(tree_data)


def search_people_api(request):
    """API endpoint for person search (for relationship forms)"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    people = Person.objects.filter(
        models.Q(first_name__icontains=query) |
        models.Q(last_name__icontains=query)
    )[:10]
    
    results = []
    for person in people:
        results.append({
            'id': person.pk,
            'text': person.full_name_reversed(),
            'birth_date': person.birth_date.strftime('%Y-%m-%d') if person.birth_date else None,
            'death_date': person.death_date.strftime('%Y-%m-%d') if person.death_date else None,
        })
    
    return JsonResponse({'results': results})
