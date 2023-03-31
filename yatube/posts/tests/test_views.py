import random
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Follow, Group, Post

User = get_user_model()
NEW_POSTS = random.randrange(settings.NUMBER_POSTS, 2 * settings.NUMBER_POSTS)
POSTS_ON_SECOND_PAGE = NEW_POSTS - settings.NUMBER_POSTS

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create_user(username="auth")
        cls.guest = User.objects.create_user(username="NoName")
        cls.follower = User.objects.create_user(username="follower")
        cls.follow_author = User.objects.create_user(
            username="following_author"
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_slug",
            description="Тестовое описание",
        )
        cls.image_png = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x00\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="image_png", content=cls.image_png, content_type="image/png"
        )
        cls.group_2 = Group.objects.create(
            title="Тестовая группа2",
            slug="test_slug_2",
            description="Тестовое описание2",
        )
        cls.post = Post.objects.create(
            text="Тестовый пост",
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.client_follower = Client()
        self.client_follower.force_login(self.follower)

    def _get_context(self, first_object, post):
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, post.text)
        self.assertEqual(post_author_0, post.author)
        self.assertEqual(post_group_0, post.group)
        self.assertEqual(post_image_0, post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            "posts/index.html": reverse("posts:index"),
            "posts/group_list.html": reverse(
                "posts:group_list",
                kwargs={"slug": self.group.slug},
            ),
            "posts/profile.html": reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ),
            "posts/post_detail.html": reverse(
                "posts:post_detail",
                kwargs={"post_id": self.post.id},
            ),
            "posts/create_post.html": reverse("posts:post_create"),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        self.assertTemplateUsed(response, "posts/create_post.html")

    def test_index_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse("posts:index"))
        first_object = response.context["page_obj"][0]
        self._get_context(first_object, self.post)

    def test_group_posts_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        first_object = response.context["page_obj"][0]
        self._get_context(first_object, self.post)

    def test_profile_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse(
                "posts:profile",
                kwargs={"username": self.post.author},
            )
        )
        first_object = response.context["page_obj"][0]
        self._get_context(first_object, self.post)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        first_object = response.context["post"]
        self._get_context(first_object, self.post)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        self.assertIsInstance(response.context.get("form"), PostForm)
        self.assertFalse(response.context["is_edit"])

    def test_post_edit_show_correct_context(self):
        """Шаблон post_create.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        self.assertIsInstance(response.context.get("form"), PostForm)
        self.assertTrue(response.context["is_edit"])

    def test_group(self):
        """Проверяем принадлежгость поста к группе."""
        response = self.guest_client.get(
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group_2.slug},
            )
        )
        object = response.context.get("page_obj").object_list
        self.assertEqual(len(object), 0)

    def test_add_comment(self):
        """Проверяем правильность добавления комментария к посту."""
        comments_count = Comment.objects.count()
        form_data = {"text": "Тестовый комментарий"}
        self.guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text=form_data["text"]).exists()
        )

    def test_index_caches(self):
        """Страница index кешируется."""
        response = self.authorized_client.get(reverse("posts:index"))
        Post.objects.all().delete()
        response_1 = self.authorized_client.get(reverse("posts:index"))
        cache.clear()
        response_2 = self.authorized_client.get(reverse("posts:index"))
        self.assertEqual(response.content, response_1.content)
        self.assertNotEqual(response_1.content, response_2.content)

    def test_follow_index_page(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется у других пользователей."""
        follow_author_post = Post.objects.create(
            text="Тестовый текст поста 1",
            author=self.follow_author,
            group=self.group,
        )
        Follow.objects.create(user=self.follower, author=self.follow_author)
        self.client_follower.get(
            reverse(
                "posts:profile_follow", kwargs={"username": self.follow_author}
            )
        )
        follower_response = self.client_follower.get(
            reverse("posts:follow_index")
        )
        first_object = follower_response.context["page_obj"]
        self.assertIn(
            follow_author_post,
            first_object,
            "подписка на автора не оформлена",
        )
        response = self.authorized_client.get(reverse("posts:follow_index"))
        object = response.context["page_obj"]
        self.assertNotIn(
            follow_author_post,
            object,
            "подписка на автора оформлена",
        )
        self.client_follower.get(
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": self.follow_author},
            )
        )
        Follow.objects.filter(
            user=self.follower, author=self.follow_author
        ).delete()
        follower_response = self.client_follower.get(
            reverse("posts:follow_index")
        )
        first_object = follower_response.context["page_obj"]
        self.assertNotIn(
            follow_author_post,
            first_object,
            "подписка на автора оформлена",
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="1",
            description="Тестовое описание",
        )
        posts = [
            Post(text=f"Тестовый пост {i}", author=cls.user, group=cls.group)
            for i in range(NEW_POSTS)
        ]
        cls.post = Post.objects.bulk_create(posts)

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_index(self):
        response = self.guest_client.get(reverse("posts:index"))
        self.assertEqual(
            len(response.context["page_obj"]), settings.NUMBER_POSTS
        )

    def test_second_page_index(self):
        response = self.guest_client.get(reverse("posts:index") + "?page=2")
        self.assertEqual(
            len(response.context["page_obj"]), POSTS_ON_SECOND_PAGE
        )

    def test_first_page_group_posts(self):
        response = self.guest_client.get(
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group.slug},
            )
        )
        self.assertEqual(
            len(response.context["page_obj"]), settings.NUMBER_POSTS
        )

    def test_second_page_group_posts(self):
        response = self.guest_client.get(
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group.slug},
            )
            + "?page=2",
        )
        self.assertEqual(
            len(response.context["page_obj"]), POSTS_ON_SECOND_PAGE
        )

    def test_first_page_profile(self):
        response = self.guest_client.get(
            reverse(
                "posts:profile",
                kwargs={"username": self.user.username},
            )
        )
        self.assertEqual(
            len(response.context["page_obj"]), settings.NUMBER_POSTS
        )

    def test_second_page_profile(self):
        response = self.guest_client.get(
            reverse(
                "posts:profile",
                kwargs={"username": self.user.username},
            )
            + "?page=2",
        )
        self.assertEqual(
            len(response.context["page_obj"]), POSTS_ON_SECOND_PAGE
        )
