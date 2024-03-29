import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group_3 = Group.objects.create(
            title="Тестовая группа3",
            slug="test_slug_3",
            description="Тестовое описание",
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_form_post_create(self):
        """Проверка функции post_create."""
        posts_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Тестовый пост2",
            "group": self.group_3.id,
            "image": uploaded,
        }
        self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                group=form_data["group"],
                image="posts/small.gif",
            ).exists()
        )

    def test_form_post_edit(self):
        """Проверка функции post_edit."""
        self.post_3 = Post.objects.create(
            text="Тестовый пост3",
            author=self.user,
            group=self.group_3,
        )
        form_data = {
            "text": "Отредактированный пост",
            "group": self.group_3.id,
        }
        self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post_3.id}),
            data=form_data,
            follow=True,
        )
        self.post_3.refresh_from_db()
        self.assertEqual(self.post_3.text, form_data["text"])
        self.assertEqual(self.post_3.group.id, form_data["group"])
