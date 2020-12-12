import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем временную папку для медиа-файлов;
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = get_user_model().objects.create_user(username="TestUser")

        cls.group = Group.objects.create(title="Группа для теста",
                                         slug="group_for_test",
                                         description="Группа для теста")

        cls.post = Post.objects.create(text="Информативный тестовый пост",
                                       author=cls.user,
                                       group=cls.group
                                       )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Рекурсивно удаляем временную после завершения тестов
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_group_label(self):
        group_label = PostFormTest.form.fields["group"].label
        self.assertEqual(group_label, "Группа поста")

    def test_text_label(self):
        text_label = PostFormTest.form.fields["text"].label
        self.assertEqual(text_label, "Текст поста")

    def test_group_help_text(self):
        group_help_text = PostFormTest.form.fields["group"].help_text
        self.assertEqual(group_help_text,
                         "Укажите в какую группу опубликовать пост")

    def test_text_help_text(self):
        text_help_text = PostFormTest.form.fields["text"].help_text
        self.assertEqual(text_help_text,
                         "Напишите ваш пост здесь")

    def test_create_post_in_group(self):
        form_data = {
            "group": PostFormTest.group.id,
            "text": "Тестовый текст"
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse("new_post"),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse("index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post_in_group(self):
        form_data = {
            "group": PostFormTest.post.group,
            "text": PostFormTest.post.text + "_updated!"
        }
        self.authorized_client.post(
            reverse("post_edit", kwargs={"username":
                                         PostFormTest.user.username,
                                         "post_id": PostFormTest.post.id}),
            data=form_data, follow=True)
        self.assertEqual(form_data["text"],
                         PostFormTest.post.text + "_updated!")

    def test_load_image_in_post(self):
        post_before = Post.objects.count()
        small_pic = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00"
            b"\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00"
            b"\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif",
            content=small_pic,
            content_type="image/gif"
        )
        form_data = {
            "group": PostFormTest.group.id,
            "text": "Еще один пост с картинкой",
            "image": uploaded}
        response = self.authorized_client.post(reverse("new_post"),
                                               data=form_data, follow=True)
        post = response.context["page"][0]
        self.assertEqual(Post.objects.count(), post_before + 1)
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(post.author, PostFormTest.user)
        self.assertRedirects(response, reverse("index"))
        self.assertEqual(post.image.size, form_data["image"].size)

    def test_users_and_comments(self):
        form_data = {"text": "Новый комментарий"}
        params = {"username": PostFormTest.user.username,
                  "post_id": PostFormTest.post.id}
        # оставляем комментарий из под авторизованного клиента
        response_auth = self.authorized_client.post(
            reverse("add_comment", kwargs=params),
            data=form_data, follow=True)

        self.assertEqual(response_auth.context["comments"][0].text,
                         form_data["text"])
        self.assertEqual(response_auth.context["comments"][0].author,
                         PostFormTest.user)
        self.assertTrue(response_auth.context.get("comments", False))

        # оставляем комментарий из под анонима
        response_not_auth = self.guest_client.post(
            reverse("add_comment", kwargs=params),
            data=form_data, follow=True)
        self.assertFalse(response_not_auth.context.get("comments", False))
