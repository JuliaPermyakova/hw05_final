from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from ..models import Post, Group, User, Comment


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text="Тестовый комментарий",
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """При отправке валидной формы создания
        поста создаётся новая запись в бд."""
        post_count = Post.objects.count()
        form_data = {"text": "Добавляем текст", "group": self.group.id}
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse(
                "posts:profile", kwargs={"username": self.user.username})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                author=self.user,
                group=self.group.id,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post(self):
        """При редактирование происходит изменение в бд."""
        post_count = Post.objects.count()
        form_data = {"text": "Редактируем текст", "group": self.group.id}
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                author=self.user,
                group=self.group.id,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_client_not_authorized(self):
        post_count = Post.objects.count()
        form_data = {"text": "Добавляем текст", "group": self.group.id}
        response = self.guest_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(response, "/auth/login/?next=/create/")
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data["text"],
                author=self.user,
                group=self.group.id,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comment_correct_form(self):
        """Валидная форма комментария создает запись в Post."""
        comments_count = Comment.objects.count()
        form_data = {"text": "Тестовый комментарий"}
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text=form_data["text"]).exists()
        )
