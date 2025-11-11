from django.core.management.base import BaseCommand

from apps.users.models import Software


class Command(BaseCommand):
    help = "Populate the database with common software tools"

    def handle(self, *args, **options):
        software_list = [
            {"name": "Optimo Route", "icon": "fa-route", "category": "Route Planning", "order": 1},
            {"name": "Xero", "icon": "fa-calculator", "category": "Accounting", "order": 2},
            {"name": "Google Ads", "icon": "fa-bullhorn", "category": "Marketing", "order": 3},
            {"name": "Excel", "icon": "fa-file-excel", "category": "Spreadsheets", "order": 4},
            {"name": "WhatsApp", "icon": "fa-whatsapp", "category": "Communication", "order": 5},
            {"name": "Connect Teams", "icon": "fa-users", "category": "Communication", "order": 6},
            {"name": "Slack", "icon": "fa-slack", "category": "Communication", "order": 7},
            {"name": "QuickBooks", "icon": "fa-book", "category": "Accounting", "order": 8},
            {"name": "Salesforce", "icon": "fa-cloud", "category": "CRM", "order": 9},
            {"name": "HubSpot", "icon": "fa-chart-line", "category": "CRM", "order": 10},
            {"name": "Mailchimp", "icon": "fa-envelope", "category": "Marketing", "order": 11},
            {"name": "Shopify", "icon": "fa-shopping-cart", "category": "E-commerce", "order": 12},
            {"name": "Google Sheets", "icon": "fa-table", "category": "Spreadsheets", "order": 13},
            {"name": "Asana", "icon": "fa-tasks", "category": "Project Management", "order": 14},
            {"name": "Trello", "icon": "fa-columns", "category": "Project Management", "order": 15},
            {"name": "Zoom", "icon": "fa-video", "category": "Communication", "order": 16},
            {"name": "Google Analytics", "icon": "fa-chart-bar", "category": "Analytics", "order": 17},
            {"name": "Stripe", "icon": "fa-credit-card", "category": "Payments", "order": 18},
        ]

        created_count = 0
        updated_count = 0

        for software_data in software_list:
            software, created = Software.objects.update_or_create(
                name=software_data["name"],
                defaults={
                    "icon": software_data["icon"],
                    "category": software_data["category"],
                    "order": software_data["order"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {software.name}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated: {software.name}"))

        self.stdout.write(
            self.style.SUCCESS(f"\nDone! Created {created_count} software entries, updated {updated_count}.")
        )

