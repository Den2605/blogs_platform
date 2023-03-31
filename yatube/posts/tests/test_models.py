from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        title = group.title
        self.assertEqual(
            title, str(group), "Ошибка в методе __str__ объекта класса Group"
        )
        post = PostModelTest.post
        text = post.text[:15]
        self.assertEqual(
            text, str(post), "Ошибка в методе __str__ объекта класса Post"
        )
