from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.guest = User.objects.create_user(username="NoName")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            text="Тестовый пост",
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.guest)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_urls(self):
        """URL- адрес использует соответствующий шаблон."""
        url_names = {
            "/": HTTPStatus.OK,
            f"/group/{self.group.slug}/": HTTPStatus.OK,
            f"/profile/{self.user.username}/": HTTPStatus.OK,
            f"/posts/{self.post.id}/": HTTPStatus.OK,
            "/unexisting_page/": HTTPStatus.NOT_FOUND,
        }
        for url, code in url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_post_create_url(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url(self):
        """Страница /posts/id/edit/ доступна только для автора поста."""
        response = self.authorized_client_author.get(
            f"/posts/{self.post.id}/edit/"
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect(self):
        """Страница /posts/id/edit/"""
        response = self.authorized_client.get(
            f"/posts/{self.post.id}/edit/", follow=True
        )
        self.assertRedirects(response, f"/posts/{self.post.id}/")

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            "/": "posts/index.html",
            f"/group/{self.group.slug}/": "posts/group_list.html",
            f"/profile/{self.user.username}/": "posts/profile.html",
            f"/posts/{self.post.id}/": "posts/post_detail.html",
            "/create/": "posts/create_post.html",
            "/unexisting_page/": "core/404.html",
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
