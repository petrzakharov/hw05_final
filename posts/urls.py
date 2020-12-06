from django.urls import path

from . import views

urlpatterns = [
    path("404/", views.page_not_found, name="Error_404"),
    path("500/", views.server_error, name="Error_500"),
    path("", views.index, name="index"),
    path("group/<slug:slug>/", views.group_posts, name="group_list"),
    path("new/", views.new_post, name="new_post"),
    path("<username>/<int:post_id>/comment",
         views.add_comment, name="add_comment"),
    path("<str:username>/", views.profile, name="profile"),
    path("<str:username>/<int:post_id>/", views.post_view, name="post"),
    path(
        "<str:username>/<int:post_id>/edit/",
        views.post_edit, name="post_edit"
    ),

]
