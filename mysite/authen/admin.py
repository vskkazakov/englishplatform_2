from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    def get_role(self, obj):
        return obj.userprofile.role if hasattr(obj, 'userprofile') else "-"
    get_role.short_description = 'Роль'
    list_display = BaseUserAdmin.list_display + ('get_role',)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# (Дополнительно — чтобы UserProfile был отдельной таблицей в админке)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'birth_date')
