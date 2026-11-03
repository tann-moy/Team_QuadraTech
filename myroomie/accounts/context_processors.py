def user_role(request):
    role, unread = None, 0
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        role = profile.role if profile else None
        unread = request.user.notifications.filter(is_read=False).count()
    return {"role": role, "unread": unread}
