from django.test import TestCase

from posts.models import Group, Post, User


class TestFormFields(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="test_user",
                                            email="test@test.com",
                                            password="test")

        cls.group = Group.objects.create(title="Группа для теста",
                                         slug="group_for_test",
                                         description="Группа для теста")

        cls.post = Post.objects.create(text="Информативный тестовый пост " * 3,
                                       author=cls.user,
                                       group=cls.group)

    def test_verbose_name(self):
        post = TestFormFields.post
        field_verboses = {
            "text": "Текст поста",
            "group": "Группа"}
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        post = TestFormFields.post
        field_help_texts = {
            "text": "Поле для ввода текста поста",
            "group": "Поле для ввода группы публикции"}
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_str_group(self):
        group = TestFormFields.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_str_post(self):
        post = TestFormFields.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))
