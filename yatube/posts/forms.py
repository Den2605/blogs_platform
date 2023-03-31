from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    required_css_class = "required"

    class Meta:
        model = Post
        fields = ("text", "group", "image")


class CommentForm(forms.ModelForm):
    required_css_class = "required"

    class Meta:
        model = Comment
        fields = ("text",)
