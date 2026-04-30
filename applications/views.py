from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import ApplicationForm, ContactForm, TimelineEventForm
from .models import Application, Company, Contact, TimelineEvent

# ── Status badge colours ──────────────────────────────────────────────────────

STATUS_COLORS: dict[str, str] = {
    Application.Status.DRAFT: "bg-gray-100 text-gray-700",
    Application.Status.SENT: "bg-blue-100 text-blue-700",
    Application.Status.SEEN: "bg-purple-100 text-purple-700",
    Application.Status.PHONE_SCREEN: "bg-yellow-100 text-yellow-700",
    Application.Status.TECHNICAL: "bg-orange-100 text-orange-700",
    Application.Status.FINAL: "bg-amber-100 text-amber-700",
    Application.Status.OFFER: "bg-green-100 text-green-700",
    Application.Status.ACCEPTED: "bg-sapin-100 text-sapin-700",
    Application.Status.REJECTED: "bg-red-100 text-red-700",
    Application.Status.GHOSTED: "bg-gray-100 text-gray-500",
    Application.Status.WITHDRAWN: "bg-gray-100 text-gray-500",
}


def status_color(status: str) -> str:
    return STATUS_COLORS.get(status, "bg-gray-100 text-gray-700")


# ── Dashboard ─────────────────────────────────────────────────────────────────


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    all_apps = Application.objects.filter(user=request.user).select_related("company")
    overdue = [a for a in all_apps if a.needs_followup]
    active = [a for a in all_apps if a.is_active]
    return render(
        request,
        "applications/dashboard.html",
        {
            "overdue": overdue,
            "active": active,
            "status_color": status_color,
        },
    )


# ── List ──────────────────────────────────────────────────────────────────────


class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = "applications/list.html"
    context_object_name = "applications"
    paginate_by = 15

    def get_queryset(self) -> QuerySet[Application]:
        qs = (
            Application.objects.filter(user=self.request.user)
            .select_related("company")
            .order_by("-last_activity_at")
        )
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "")
        source = self.request.GET.get("source", "")

        if q:
            qs = qs.filter(
                Q(position_title__icontains=q) | Q(company__name__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if source:
            qs = qs.filter(source=source)
        return qs

    def get_context_data(self, **kwargs: object) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Application.Status.choices
        ctx["source_choices"] = Application.Source.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_source"] = self.request.GET.get("source", "")
        ctx["current_q"] = self.request.GET.get("q", "")
        ctx["status_color"] = status_color
        return ctx


# ── Create ────────────────────────────────────────────────────────────────────


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = "applications/form.html"

    def get_success_url(self) -> str:
        return reverse_lazy("application_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form: ApplicationForm) -> HttpResponse:
        form.instance.user = self.request.user
        messages.success(self.request, "Candidature créée avec succès.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs: object) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Nouvelle candidature"
        ctx["companies"] = Company.objects.values_list("name", flat=True)
        return ctx


# ── Detail ────────────────────────────────────────────────────────────────────


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    model = Application
    template_name = "applications/detail.html"
    context_object_name = "application"

    def get_queryset(self) -> QuerySet[Application]:
        return Application.objects.filter(user=self.request.user).select_related(
            "company"
        )

    def get_context_data(self, **kwargs: object) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Application.Status.choices
        ctx["status_color"] = status_color(self.object.status)
        ctx["tabs"] = [
            ("infos", "Infos"),
            ("notes", "Notes"),
            ("contacts", "Contacts"),
            ("timeline", "Historique"),
        ]
        return ctx


# ── Update ────────────────────────────────────────────────────────────────────


class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    model = Application
    form_class = ApplicationForm
    template_name = "applications/form.html"

    def get_queryset(self) -> QuerySet[Application]:
        return Application.objects.filter(user=self.request.user)

    def get_success_url(self) -> str:
        return reverse_lazy("application_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form: ApplicationForm) -> HttpResponse:
        messages.success(self.request, "Candidature mise à jour.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs: object) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Modifier — {self.object}"
        ctx["companies"] = Company.objects.values_list("name", flat=True)
        return ctx


# ── Inline status change (htmx) ───────────────────────────────────────────────


@login_required
def application_status_update(request: HttpRequest, pk: int) -> HttpResponse:
    application = get_object_or_404(Application, pk=pk, user=request.user)
    if request.method == "POST":
        new_status = request.POST.get("status", "")
        valid = {s for s, _ in Application.Status.choices}
        if new_status in valid:
            application.status = new_status
            application.save()
        return render(
            request,
            "applications/partials/status_badge.html",
            {
                "application": application,
                "status_color": status_color(application.status),
                "status_choices": Application.Status.choices,
            },
        )
    # GET → show inline select form
    return render(
        request,
        "applications/partials/status_select.html",
        {
            "application": application,
            "status_choices": Application.Status.choices,
        },
    )


# ── Contacts (htmx) ───────────────────────────────────────────────────────────


def _get_application(request: HttpRequest, pk: int) -> Application:
    return get_object_or_404(Application, pk=pk, user=request.user)


def _render_contacts_list(
    request: HttpRequest, application: Application
) -> HttpResponse:
    return render(
        request,
        "applications/partials/contacts_list.html",
        {"application": application},
    )


@login_required
def contact_create(request: HttpRequest, pk: int) -> HttpResponse:
    application = _get_application(request, pk)
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.application = application
            contact.save()
            return _render_contacts_list(request, application)
    else:
        form = ContactForm()
    return render(
        request,
        "applications/partials/contact_form.html",
        {"form": form, "application": application, "action": "create"},
    )


@login_required
def contact_update(request: HttpRequest, pk: int, contact_pk: int) -> HttpResponse:
    application = _get_application(request, pk)
    contact = get_object_or_404(Contact, pk=contact_pk, application=application)
    if request.method == "POST":
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            return _render_contacts_list(request, application)
    else:
        form = ContactForm(instance=contact)
    return render(
        request,
        "applications/partials/contact_form.html",
        {
            "form": form,
            "application": application,
            "contact": contact,
            "action": "update",
        },
    )


@login_required
def contact_delete(request: HttpRequest, pk: int, contact_pk: int) -> HttpResponse:
    application = _get_application(request, pk)
    contact = get_object_or_404(Contact, pk=contact_pk, application=application)
    if request.method == "POST":
        contact.delete()
    return _render_contacts_list(request, application)


# ── Timeline events (htmx) ────────────────────────────────────────────────────


def _render_timeline_list(
    request: HttpRequest, application: Application
) -> HttpResponse:
    return render(
        request,
        "applications/partials/timeline_list.html",
        {"application": application},
    )


@login_required
def event_create(request: HttpRequest, pk: int) -> HttpResponse:
    application = _get_application(request, pk)
    if request.method == "POST":
        form = TimelineEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.application = application
            event.save()
            application.last_activity_at = event.occurred_at
            application.save(update_fields=["last_activity_at"])
            return _render_timeline_list(request, application)
    else:
        form = TimelineEventForm()
    return render(
        request,
        "applications/partials/event_form.html",
        {"form": form, "application": application},
    )


@login_required
def event_delete(request: HttpRequest, pk: int, event_pk: int) -> HttpResponse:
    application = _get_application(request, pk)
    event = get_object_or_404(TimelineEvent, pk=event_pk, application=application)
    if request.method == "POST":
        event.delete()
    return _render_timeline_list(request, application)
