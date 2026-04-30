from django import forms

from .models import Application, Company, Contact, TimelineEvent


class ApplicationForm(forms.ModelForm):
    company_name = forms.CharField(
        max_length=200,
        label="Entreprise",
        widget=forms.TextInput(attrs={"list": "company-list", "autocomplete": "off"}),
    )

    class Meta:
        model = Application
        fields = [
            "position_title",
            "job_url",
            "location",
            "work_mode",
            "salary_min",
            "salary_max",
            "currency",
            "source",
            "status",
            "applied_at",
            "next_action_date",
            "cover_letter",
            "notes",
            "cv_file",
        ]
        widgets = {
            "applied_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "next_action_date": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "cover_letter": forms.Textarea(attrs={"rows": 4}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.company_id:
            self.fields["company_name"].initial = self.instance.company.name
        self.fields["applied_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["next_action_date"].input_formats = ["%Y-%m-%d"]

    def save(self, commit: bool = True) -> Application:
        company, _ = Company.objects.get_or_create(
            name=self.cleaned_data["company_name"].strip()
        )
        instance = super().save(commit=False)
        instance.company = company
        if commit:
            instance.save()
        return instance


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ["name", "role", "email", "phone", "linkedin", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class TimelineEventForm(forms.ModelForm):
    class Meta:
        model = TimelineEvent
        fields = ["event_type", "occurred_at", "description"]
        widgets = {
            "occurred_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["occurred_at"].input_formats = ["%Y-%m-%dT%H:%M"]
