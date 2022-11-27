import shutil
import tempfile
from django.core.cache import cache
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django import forms

from ..models import Group, Post, User, Comment, Follow


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="test_name")
        cls.no_user = User.objects.create(username="no_author")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.no_user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post.id}
            ): "posts/create_post.html",
            reverse(
                "posts:post_create",
            ): "posts/create_post.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Ожидаемый контекст в шаблоне index."""
        response = self.guest_client.get(reverse("posts:index"))
        expected = list(Post.objects.all()[:10])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_group_list_show_correct_context(self):
        """Ожидаемый контекст в шаблоне group_list."""
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        expected = list(Post.objects.filter(group_id=self.group.id)[:10])
        self.assertEqual(list(response.context["page_obj"]), expected)
        self.assertEqual(response.context.get("post").group, self.post.group)

    def test_profile_show_correct_context(self):
        """Ожидаемый контекст в шаблоне profile."""
        response = self.guest_client.get(
            reverse("posts:profile", args=(self.post.author,))
        )
        expected = list(Post.objects.filter(author_id=self.user.id)[:10])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_post_detail_show_correct_context(self):
        """Ожидаемый контекст в шаблоне post_detail."""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(response.context.get("post").text, self.post.text)
        self.assertEqual(response.context.get("post").author, self.post.author)
        self.assertEqual(response.context.get("post").group, self.post.group)
        self.assertEqual(response.context["author_posts"], Post.objects.count())

    def test_edit_show_correct_context(self):
        """Ожидаемый контекст в шаблоне create_edit."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        self.assertIn("form", response.context)
        self.assertTrue(response.context["is_edit"], True)
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get("is_edit"))

    def test_create_show_correct_context(self):
        """Ожидаемый контекст в шаблоне create."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_on_the_index(self):
        """Отображение групп на страницах"""
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ): Post.objects.get(group=self.post.group),
        }
        for reverse_name, address in form_fields.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(address, response.context["page_obj"])

    def test_check_group_not_in_mistake_group_list_page(self):
        """Добавление поста в правильную группу."""
        form_fields = {
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for reverse_name, address in form_fields.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                form_field = response.context["page_obj"]
                self.assertNotIn(address, form_field)

    def test_cache_check(self):
        """Проверка кеширования."""
        response = self.guest_client.get(reverse("posts:index"))
        Post.objects.get(id=self.post.id).delete()
        response_cache = self.guest_client.get(reverse("posts:index"))
        self.assertEqual(response.content, response_cache.content)

    def test_follow_page(self):
        """Новая запись пользователя появляется в ленте тех, кто на него подписан"""
        response = self.authorized_client_not_author.get(reverse("posts:follow_index"))
        self.assertNotIn(self.post, response.context["page_obj"])

    def test_follow(self):
        response = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context["page_obj"]), 0)
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        response_aftr = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response_aftr.context["page_obj"]), 1)
        self.assertIn(self.post, response_aftr.context["page_obj"])

    def test_unfollow(self):
        Follow.objects.all().delete()
        response = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context["page_obj"]), 0)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="test_name")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый текст", group=cls.group, image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def test_image_in_group_list_page(self):
        """Картинка передается на страницу group_list."""
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
        )
        self.assertEqual(response.context["page_obj"][0].image, self.post.image)

    def test_image_in_index_and_profile_page(self):
        """Картинка передается на страницу index_and_profile."""
        templates = (
            reverse("posts:index"),
            reverse("posts:profile", kwargs={"username": self.post.author}),
        )
        for url in templates:
            with self.subTest(url):
                response = self.guest_client.get(url)
                self.assertEqual(response.context["page_obj"][0].image, self.post.image)

    def test_image_in_post_detail_page(self):
        """Картинка передается на страницу post_detail."""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(response.context["post"].image, self.post.image)

    def test_image_in_page(self):
        """Проверяем что пост с картинкой создается в БД"""
        self.assertTrue(
            Post.objects.filter(text="Тестовый текст", image="posts/small.gif").exists()
        )
