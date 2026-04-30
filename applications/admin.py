from django.contrib import admin

from .models import Application, Company, Contact, TimelineEvent


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0
    fields = ("name", "role", "email", "phone", "linkedin")


class TimelineEventInline(admin.TabularInline):
    model = TimelineEvent
    extra = 0
    fields = ("event_type", "occurred_at", "description")
    ordering = ("-occurred_at",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "industry", "created_at")
    search_fields = ("name", "location", "industry")
    ordering = ("name",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "position_title",
        "company",
        "status",
        "source",
        "applied_at",
        "next_action_date",
        "needs_followup_display",
    )
    list_filter = ("status", "source", "work_mode", "currency")
    search_fields = ("position_title", "company__name", "location")
    raw_id_fields = ("company",)
    readonly_fields = ("created_at", "last_activity_at")
    inlines = [ContactInline, TimelineEventInline]
    date_hierarchy = "applied_at"
    fieldsets = (
        (
            "Poste",
            {
                "fields": (
                    "user",
                    "company",
                    "position_title",
                    "job_url",
                    "location",
                    "work_mode",
                )
            },
        ),
        (
            "Rémunération",
            {"fields": ("salary_min", "salary_max", "currency")},
        ),
        (
            "Statut",
            {
                "fields": (
                    "source",
                    "status",
                    "applied_at",
                    "next_action_date",
                    "last_activity_at",
                    "created_at",
                )
            },
        ),
        (
            "Documents & Notes",
            {"fields": ("cv_file", "cover_letter", "notes")},
        ),
    )

    @admin.display(boolean=True, description="À relancer")
    def needs_followup_display(self, obj: Application) -> bool:
        return obj.needs_followup


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "application", "email")
    search_fields = ("name", "role", "email", "application__position_title")
    raw_id_fields = ("application",)


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "application", "occurred_at")
    list_filter = ("event_type",)
    raw_id_fields = ("application",)
    ordering = ("-occurred_at",)
