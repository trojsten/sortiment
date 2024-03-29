from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group

from .models import CreditLog, SortimentUser


class UserCreationForm(forms.ModelForm):
    class Meta:
        model = SortimentUser
        fields = ("username", "first_name", "last_name", "barcode")


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    disabled password hash display field.
    """

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = SortimentUser
        fields = ("password", "is_active", "is_staff", "credit", "barcode")


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = (
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "credit",
        "barcode",
    )
    list_filter = ("is_staff",)
    fieldsets = (
        (None, {"fields": ("username", "password", "credit")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "barcode", "is_guest")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {"fields": ("username", "password", "credit")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "barcode", "is_guest")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    search_fields = ("first_name", "last_name", "username")
    ordering = ("username",)
    filter_horizontal = ()


admin.site.register(SortimentUser, UserAdmin)
admin.site.unregister(Group)
admin.site.register(CreditLog)
