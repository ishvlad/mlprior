from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from el_pagination.decorators import page_template
from core.forms import FeedbackForm
from django.views.generic.edit import FormView


class FeedbackView(FormView):
    template_name = 'core/feedback.html'
    form_class = FeedbackForm
    success_url = '/home'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        context['page_id'] = 'feedback'

        return context

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        print(form)
        # form.send_email()
        return super().form_valid(form)