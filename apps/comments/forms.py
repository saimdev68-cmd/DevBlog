from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    content = forms.CharField(
        label="Leave a comment",
        min_length=3,
        max_length=2000,
        widget=forms.Textarea(attrs={
            'class': 'form-input form-textarea',
            'rows': 4,
            'placeholder': 'Share your thoughts, feedback, or questions...',
            'required': True,
        }),
    )

    class Meta:
        model = Comment
        fields = ('content',)

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if len(content) < 3:
            raise forms.ValidationError("Comment must be at least 3 characters long.")
        if len(content) > 2000:
            raise forms.ValidationError("Comment cannot exceed 2000 characters.")
        return content
