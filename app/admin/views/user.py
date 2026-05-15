from admin.views.base import BaseAdminView
from models.user import User


class UserAdminView(BaseAdminView):
    model = User
    name = "User"
    name_plural = "Users"
    sortable_fields = ["id"]
