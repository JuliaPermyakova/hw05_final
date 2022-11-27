from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy("posts:index")
    template_name = "users/signup.html"


class Logout(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy("users:logout")
    template_name = "users/logged_out.html"
