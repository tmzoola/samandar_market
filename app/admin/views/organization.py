from admin.views.base import BaseAdminView
from models.organization import Organization


class OrganizationAdminView(BaseAdminView):
    model = Organization
    name = "Organization"
    name_plural = "Organizations"
    sortable_fields = ["id"]
