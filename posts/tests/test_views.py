import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage, Site
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, Follow
from yatube import settings


class PageTest(TestCase):
    """
    Тесты шаблонов проводятся в файле test_urls.py
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create_user(username="TestUser")
        cls.user_2 = get_user_model().objects.create_user(username="TestUser2")
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group = Group.objects.create(
            title="Группа для теста",
            slug="group_for_test",
            description="Группа для теста")

        cls.post = Post.objects.create(
            text="Информативный тестовый пост",
            author=cls.user,
            group=cls.group)

        cls.form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField
        }
        flat_site = Site.objects.get(pk=2)

        cls.page_about_author = FlatPage.objects.create(
            url='/about-author/',
            title='about-author',
            content='about-author'
        )

        cls.page_about_spec = FlatPage.objects.create(
            url='/about-spec/',
            title='about-spec',
            content='about-spec'
        )
        cls.page_about_author.sites.add(flat_site)
        cls.page_about_spec.sites.add(flat_site)

        cls.other_group = Group.objects.create(
            title="Еще одна группа для теста",
            slug="add_new_one_group_for_test",
            description="Еще одна группа для теста")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Рекурсивно удаляем временную директорию после завершения тестов
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(PageTest.user)

    def test_new_post_page_correct_context(self):
        response = self.authorized_client.get(reverse("new_post"))
        for value, expected in PageTest.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_correct_context(self):
        """Шаблон главной страницы с правильным контекстом"""
        response = self.authorized_client.get(reverse("index"))
        self.assertEqual(response.context.get("page")[0].id,
                         PageTest.post.id)

    def test_group_page_correct_context(self):
        response = self.authorized_client.get(
            reverse("group_list",
                    kwargs={"slug": "group_for_test"}))
        self.assertEqual(response.context.get("group").id,
                         PageTest.group.id)

    def test_created_post_appear_on_index_page(self):
        response = self.authorized_client.get(reverse("index"))
        post_from_context = response.context.get("page")[0]
        self.assertEqual(post_from_context, PageTest.post)

    def test_created_post_appear_on_group_page(self):
        response = self.authorized_client.get(
            reverse("group_list",
                    kwargs={"slug": "group_for_test"}))
        post_from_context = response.context.get("page")[0]
        self.assertEqual(post_from_context, PageTest.post,
                         msg='пост попал в корректную группу')

    def test_created_post_not_appear_on_other_group_page(self):
        response = self.authorized_client.get(
            reverse("group_list",
                    kwargs={"slug": "add_new_one_group_for_test"}))
        try:
            post_from_context = response.context.get("page")[0]
        except IndexError:
            post_from_context = None
        self.assertNotEqual(post_from_context, PageTest.post,
                            msg='пост не попал в некорректную группу')

    def test_post_edit_has_correct_context(self):
        response = self.authorized_client.get(
            reverse("post_edit", kwargs={"username": PageTest.user.username,
                                         "post_id": PageTest.post.id}))
        for value, expected in PageTest.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_user_profile_has_correct_context(self):
        response = self.authorized_client.get(
            reverse("profile", kwargs={
                "username": PageTest.user.username}))
        post_from_context = response.context.get("page")[0]
        self.assertEqual(post_from_context, PageTest.post)
        self.assertEqual(post_from_context.author, PageTest.post.author)

    def test_post_page_has_correct_context(self):
        response = self.authorized_client.get(
            reverse("post", kwargs={
                "username": PageTest.user.username,
                "post_id": PageTest.post.id}))
        post_from_context = response.context.get("post")
        self.assertEqual(post_from_context.author, PageTest.post.author)
        self.assertEqual(post_from_context, PageTest.post)

    def test_paginator_on_index_page(self):
        response = self.authorized_client.get(reverse("index"))
        self.assertEqual(response.context.get("paginator").num_pages, 1)

    def test_flatpage_about_author_has_correct_context(self):
        response = self.authorized_client.get(PageTest.page_about_author.url)
        self.assertEqual(response.context.get("flatpage").id,
                         PageTest.page_about_author.id)

    def test_flatpage_about_spec_has_correct_context(self):
        response = self.authorized_client.get(PageTest.page_about_spec.url)
        self.assertEqual(response.context.get("flatpage").id,
                         PageTest.page_about_spec.id)

    def test_follow_user(self):
        params = {"username": PageTest.user_2.username}
        # follow
        self.authorized_client.get(reverse("profile_follow", kwargs=params))
        # подписка существует
        self.assertTrue(Follow.objects.filter(author=PageTest.user_2,
                                              user=PageTest.user).exists())

    def test_unfollow_user(self):
        params = {"username": PageTest.user_2.username}
        self.authorized_client.get(reverse("profile_follow", kwargs=params))
        # unfollow
        self.authorized_client.get(reverse("profile_unfollow", kwargs=params))
        # подписка несуществует
        self.assertFalse(Follow.objects.filter(author=PageTest.user_2,
                                               user=PageTest.user).exists())

    def test_post_appear_on_favorite_author_page_after_follow(self):
        self.authorized_client.force_login(PageTest.user_2)
        params = {"username": PageTest.user.username}
        # user_2 подписался на user (у него уже есть пост в атрибуте класса)
        self.authorized_client.get(reverse("profile_follow", kwargs=params))
        # получаем страницу для user_2
        response_follow = self.authorized_client.get(reverse("follow_index"))
        self.assertEqual(response_follow.context["post"].id, PageTest.post.id)

        # user_2 отписывается от user (пост должен пропасть)
        self.authorized_client.get(reverse("profile_unfollow", kwargs=params))
        response_unfollow = self.authorized_client.get(reverse("follow_index"))
        # объекта пост на странице follow_index не существует
        self.assertFalse(response_unfollow.get("post", False))
