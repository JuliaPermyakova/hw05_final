from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post, User, Comment, Follow

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="auth")
        cls.no_user = User.objects.create(username="no_author")
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
        self.authorized_client.force_login(PostURLTests.user)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.no_user)

    def test_urls_for_guests(self):
        """Страницы доступные любому пользователю."""
        free_urls = (
            "/",
            f"/group/{self.group.slug}/",
            f"/profile/{self.user.username}/",
            f"/posts/{self.post.id}/",
        )
        for address in free_urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_list_url_exists_at_desired_location(self):
        """Страница доступна авторизованному пользователю."""
        response = self.authorized_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_only_for_author(self):
        """Страница редактирования поста, доступная только автору."""
        response = self.authorized_client.get(f"/posts/{self.post.id}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_edit_only_for_author(self):
        response = self.authorized_client_not_author.get(
            f"/posts/{self.post.id}/edit/", follow=True
        )
        self.assertRedirects(response, f"/posts/{self.post.id}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_anonymous_on_admin_login(self):
        """Страница перенаправит анонимного пользователя на страницу логина."""
        response = self.guest_client.get("/create/", follow=True)
        self.assertRedirects(response, "/auth/login/?next=/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_at_desired_location(self):
        """Страница /unexisting_page/ должна выдать ошибку."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            "/": "posts/index.html",
            f"/group/{self.group.slug}/": "posts/group_list.html",
            f"/profile/{self.user.username}/": "posts/profile.html",
            f"/posts/{self.post.id}/": "posts/post_detail.html",
            f"/posts/{self.post.id}/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_comment_only_for_authorized_client(self):
        """Комментирование доступно только для авторизованных"""
        response = self.guest_client.get(f"/posts/{self.post.id}/comment/", follow=True)
        self.assertRedirects(
            response, f"/auth/login/?next=/posts/{self.post.id}/comment/"
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
