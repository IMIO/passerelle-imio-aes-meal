from django.views.generic import View, CreateView, DeleteView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.core.urlresolvers import reverse

from .models import ImioTs1Datasources, MotivationTerm, DestinationTerm


class DatasourcesView(View, SingleObjectMixin):
    model = ImioTs1Datasources


class MotivationtermAddView(CreateView):
    model = MotivationTerm
    fields = '__all__'
    template_name = 'passerelle_imio_ts1_datasources/motivationterm_form.html'

    def get_success_url(self):
        connector = ImioTs1Datasources.objects.get(slug=self.kwargs['connector_slug'])
        return reverse('view-connector',
                kwargs={'connector': connector.get_connector_slug(),
                        'slug': connector.slug})


class MotivationtermDeleteView(DeleteView):
    model = MotivationTerm

    def get_success_url(self):
        connector = ImioTs1Datasources.objects.get(slug=self.kwargs['connector_slug'])
        return reverse('view-connector',
                kwargs={'connector': connector.get_connector_slug(),
                        'slug': connector.slug})


class MotivationtermUpdateView(UpdateView):
    model = MotivationTerm
    fields = '__all__'

    def get_success_url(self):
        connector = ImioTs1Datasources.objects.get(slug=self.kwargs['connector_slug'])
        return reverse('view-connector',
                kwargs={'connector': connector.get_connector_slug(),
                        'slug': connector.slug})


class DestinationtermAddView(CreateView):
    model = DestinationTerm
    fields = '__all__'
    template_name = 'passerelle_imio_ts1_datasources/destinationterm_form.html'

    def get_success_url(self):
        connector = ImioTs1Datasources.objects.get(slug=self.kwargs['connector_slug'])
        return reverse('view-connector',
                kwargs={'connector': connector.get_connector_slug(),
                        'slug': connector.slug})


class DestinationtermDeleteView(DeleteView):
    model = DestinationTerm

    def get_success_url(self):
        connector = ImioTs1Datasources.objects.get(slug=self.kwargs['connector_slug'])
        return reverse('view-connector',
                kwargs={'connector': connector.get_connector_slug(),
                        'slug': connector.slug})


class DestinationtermUpdateView(UpdateView):
    model = DestinationTerm
    fields = '__all__'

    def get_success_url(self):
        connector = ImioTs1Datasources.objects.get(slug=self.kwargs['connector_slug'])
        return reverse('view-connector',
                kwargs={'connector': connector.get_connector_slug(),
                        'slug': connector.slug})
