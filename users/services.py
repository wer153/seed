from django.contrib.auth import get_user_model
from django.db.transaction import atomic

from users.models import User as AuthUser, Profile, Following
from users.operations import generate_nick_name

User: AuthUser = get_user_model()


def signup(
    email: str,
    image: str,
    nick_name: str,
) -> AuthUser:
    if not nick_name:
        nick_name = generate_nick_name()
    with atomic():
        password = User.objects.make_random_password()
        user = User.objects.create(email=email, password=password)
        Profile.objects.create(user=user, nick_name=nick_name, image=image)
    return user


def follow(from_: Profile, to: Profile) -> Following:
    return Following.objects.create(following=from_, follower=to)
