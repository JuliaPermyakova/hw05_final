from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название группы")
    slug = models.SlugField(max_length=250, unique=True, verbose_name="URL")
    description = models.TextField(verbose_name="Описание")

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст поста")
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name="Дата публикации")
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
        verbose_name="Группа",
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts",
        verbose_name="Автор"
    )
    image = models.ImageField(verbose_name="Картинка", upload_to="posts/",
                              blank=True)

    def __str__(self) -> str:
        return self.text[:15]

    class Meta:
        ordering = ["-pub_date"]


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.SET_NULL, related_name="comments", blank=True,
        null=True
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments")
    text = models.TextField(
        verbose_name="Текст комментария", help_text="Введите текст комментария"
    )
    created = models.DateTimeField(verbose_name="Дата публикации",
                                   auto_now_add=True)

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following")
