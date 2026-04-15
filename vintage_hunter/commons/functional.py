from django.core.exceptions import PermissionDenied


def is_staff(user):
    return user.is_authenticated and user.is_staff

def is_not_staff(user):
    return user.is_authenticated and not user.is_staff