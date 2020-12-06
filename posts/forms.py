from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")
        labels = {"text": "Текст поста", "group": "Группа поста"}
        help_texts = {"text": "Напишите ваш пост здесь",
                      "group": "Укажите в какую группу опубликовать пост"}


class CommentForm(forms.ModelForm):
    def clean_text(self):
        data = self.cleaned_data["text"]
        if "плохой коммент" in data.lower():
            raise forms.ValidationError("Айяйяй!")
        return data

    class Meta:
        model = Comment
        fields = ("text",)
