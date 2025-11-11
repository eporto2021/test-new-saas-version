from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from health_check.views import MainView

from apps.users.models import Software


def home(request):
    if request.user.is_authenticated:
        software_list = Software.objects.filter(is_active=True)
        return render(
            request,
            "web/app_home.html",
            context={
                "active_tab": "dashboard",
                "page_title": _("Dashboard"),
                "software_list": software_list,
                "show_software_survey": not request.user.completed_software_survey,
            },
        )
    else:
        return render(request, "web/landing_page.html")


@login_required
@require_POST
def submit_software_survey(request):
    """Handle the software survey form submission."""
    software_ids = request.POST.getlist("software")
    custom_software = request.POST.get("custom_software", "").strip()
    
    # Update user's software tools
    request.user.software_tools.set(software_ids)
    request.user.custom_software = custom_software
    request.user.completed_software_survey = True
    request.user.save()
    
    messages.success(request, _("Thank you! Your software preferences have been saved."))
    return redirect("web:home")


def simulate_error(request):
    raise Exception("This is a simulated error.")


class HealthCheck(MainView):
    def get(self, request, *args, **kwargs):
        tokens = settings.HEALTH_CHECK_TOKENS
        if tokens and request.GET.get("token") not in tokens:
            raise Http404
        return super().get(request, *args, **kwargs)
