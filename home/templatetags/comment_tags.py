from django import template

register = template.Library()

@register.filter
def is_comment_liked(comment, user):
    """Check if a comment is liked by the given user"""
    if not user:
        return False
    # user is already an Author object when passed from views
    return comment.is_liked_by_user(user)

