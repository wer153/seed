from datetime import date

from django.shortcuts import get_object_or_404
from django.utils.timezone import localdate
from ninja import Router, UploadedFile
from ninja.errors import ValidationError
from ninja.security import django_auth

from calenders.dtos import PostListOut, PostDetailOut, Emoji, CreateCalenderOut, CalenderListOut, CalenderDetailOut
from calenders.models import Post, Calender

router = Router(auth=django_auth)


@router.get('', response=list[CalenderListOut])
def get_calender_list(request) -> list[CalenderListOut]:
    calenders = Calender.objects.filter(owner=request.user)
    return [CalenderListOut(id=str(calender.id),  joined_date=calender.joined_date) for calender in calenders]


@router.post('', response=CalenderDetailOut)
def create_calender(request) -> CreateCalenderOut:
    count = Calender.objects.filter(owner=request.user).count()
    if Calender.MAX_COUNT <= count:
        raise ValidationError(errors=f'calender count exceeds max count {count}/{Calender.MAX_COUNT}')
    calender = Calender.objects.create(owner=request.user, joined_date=localdate())
    return CalenderDetailOut(id=str(calender.id), joined_date=calender.joined_date)


@router.get('/{calender_id}/posts', response=list[PostListOut])
def get_post_list(request, calender_id: str, start_date: date | None = None, end_date: date | None = None):
    date_filter = {}
    if start_date:
        date_filter |= {'post_date__gte': start_date}
    if end_date:
        date_filter |= {'post_date__lt': end_date}
    posts = Post.objects.filter(
        calender=calender_id,
        user=request.user,
        **date_filter,
    )
    return [
        PostListOut(
            id=str(post.id),
            thumbnail=post.thumbnail.url,
            post_date=post.post_date,
            emoji=post.emoji,
        )
        for post in posts
    ]


@router.get('/{calender_id}/posts/{post_date}', response=PostDetailOut)
def get_post_detail(request, calender_id: str, post_date: date):
    post: Post = get_object_or_404(
        Post,
        post_date=post_date,
        user=request.user,
        calender=calender_id,
    )
    return PostDetailOut(
        id=str(post.id),
        image=post.image.url,
        post_date=post.post_date,
        emoji=post.emoji,
    )


@router.post('/{calender_id}/posts/{post_date}', response={200: PostDetailOut, 201: PostDetailOut})
def put_post_detail(
    request,
    calender_id: str,
    post_date: date,
    images: list[UploadedFile],
    emoji: Emoji | None = None,
):
    emoji = emoji.value if emoji else ''
    image = images[0]
    calender = Calender.objects.get(id=calender_id)
    post, created = Post.objects.update_or_create(
        calender=calender,
        post_date=post_date,
        user=request.user,
        defaults={
            'calender': calender,
            'post_date': post_date,
            'user': request.user,
            'emoji': emoji,
        },
    )
    post.image = image
    post.thumbnail = post.image
    post.save()
    status_code = 201 if created else 200
    return status_code, PostDetailOut(
        id=str(post.id),
        image=post.image.url,
        post_date=post.post_date,
        emoji=post.emoji,
    )


@router.delete('/{calender_id}/posts/{post_date}')
def delete_post_detail(request, calender_id: str, post_date: date):
    post: Post = get_object_or_404(
        Post,
        post_date=post_date,
        user=request.user,
        calender=calender_id,
    )
    post.delete()
    return None
