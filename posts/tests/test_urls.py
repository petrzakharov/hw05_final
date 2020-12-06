from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage, Site
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post
from datetime import datetime


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        site = Site.objects.get(pk=2)
        self.page_about_author = FlatPage.objects.create(
            url='/about-author/',
            title='about-author',
            content='about-author'
        )
        self.page_about_spec = FlatPage.objects.create(
            url='/about-spec/',
            title='about-spec',
            content='about-spec'
        )
        self.page_about_author.sites.add(site)
        self.page_about_spec.sites.add(site)

    def test_about(self):
        """
        Тестирование страницы Об авторе
        """
        response = self.guest_client.get(self.page_about_author.url)
        self.assertEqual(response.status_code, 200)

    def test_tech(self):
        """
        Тестирование страницы Технологии
        """
        response = self.guest_client.get(self.page_about_spec.url)
        self.assertEqual(response.status_code, 200)


class NoStaticURLTests(TestCase):
    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(NoStaticURLTests.user)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create_user(username="TestUser")
        cls.user_without_posts = (
            get_user_model().objects.create_user(username="user_without_posts")
        )

        cls.group = Group.objects.create(title="Группа для теста",
                                         slug="group_for_test",
                                         description="Группа для теста")
        cls.post = Post.objects.create(text="Test post",
                                       author=cls.user)

        cls.all_urls = (
            dict(
                authorized_user={
                    reverse("index"): 200,
                    reverse("new_post"): 200,
                    reverse("group_list",
                            kwargs={"slug": cls.group.slug}): 200,
                    reverse("profile", kwargs={"username":
                                               cls.user.username}): 200,
                    reverse("post", kwargs={"username":
                                            cls.user.username,
                                            "post_id": cls.post.id}): 200,
                    reverse("post_edit", kwargs={"username":
                                                 cls.user.username,
                                                 "post_id": cls.post.id}): 200,
                },
                anonymous_user={
                    reverse("new_post"): 302,
                    reverse("post_edit", kwargs={"username":
                                                 cls.user.username,
                                                 "post_id": cls.post.id}): 302
                }))
        cls.templates_url = (
            {
                "index.html":
                    reverse("index"),
                "group.html":
                    reverse("group_list", kwargs={"slug": cls.group.slug}),
                "new.html":
                    reverse("new_post"),
                "new.html":
                    reverse("post_edit", kwargs={"username":
                                                 cls.user.username,
                                                 "post_id": cls.post.id}),
                "profile.html":
                    reverse("profile", kwargs={"username":
                                               cls.user.username}),
            })
        cls.post_edit_url = list(
            cls.all_urls["authorized_user"].items())[-1][0]

    def test_urls_response_anonymous_user(self):
        for url, code in (NoStaticURLTests.all_urls["anonymous_user"]).items():
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code, url)

    def test_urls_response_authorized_user(self):
        for url, code in (
                (NoStaticURLTests.all_urls["authorized_user"]).items()):
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, code, url)

    def test_urls_uses_correct_template(self):
        for template, url in NoStaticURLTests.templates_url.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template, url)

    def test_redirect_for_edit_post_anonymous_user(self):
        response = self.guest_client.get(NoStaticURLTests.post_edit_url)
        url_redirect = reverse("post",
                               kwargs={"username":
                                       NoStaticURLTests.user.username,
                                       "post_id": NoStaticURLTests.post.id})
        self.assertRedirects(response, url_redirect)

    def test_url_response_for_edit_post_under_no_author_user(self):
        self.authorized_client.force_login(
            NoStaticURLTests.user_without_posts)
        url = NoStaticURLTests.post_edit_url
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, 302, url)

    def test_redirect_for_edit_post_under_no_author_user(self):
        self.authorized_client.force_login(
            NoStaticURLTests.user_without_posts)
        response = self.authorized_client.get(NoStaticURLTests.post_edit_url)
        url_redirect = reverse("post",
                               kwargs={"username":
                                       NoStaticURLTests.user.username,
                                       "post_id": NoStaticURLTests.post.id})
        self.assertRedirects(response, url_redirect)

    def test_404_error_raise(self):
        response = self.authorized_client.get(hash(datetime.now()))
        response_default_page_404 = self.authorized_client.get(
            reverse("Error_404"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response_default_page_404.status_code, 404)

    def test_500_error_raise(self):
        response_default_page_500 = self.authorized_client.get(
            reverse("Error_500"))
        self.assertEqual(response_default_page_500.status_code, 500)

    def test_cache_on_index_page(self):
        NoStaticURLTests.post.text = 'Text was updated in test post!'
        response = self.authorized_client.get(reverse("index"))
        text_post_from_context = response.context.get("page")[0].text
        self.assertNotEqual(text_post_from_context, NoStaticURLTests.post.text)
