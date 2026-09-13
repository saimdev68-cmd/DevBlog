from django import forms
from .models import Category, Post, Tag


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title',
            'category',
            'tags',
            'excerpt',
            'content',
            'featured_image',
            'status',
            'is_featured',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter a captivating, descriptive article title...',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 4,
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-input form-textarea',
                'rows': 3,
                'placeholder': 'Short summary for SEO and preview cards (optional, auto-generated if empty)...',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-input form-textarea',
                'rows': 14,
                'placeholder': 'Write your markdown or HTML content here...',
            }),
            'featured_image': forms.ClearableFileInput(attrs={
                'class': 'form-file-input',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }

    def clean_featured_image(self):
        image = self.cleaned_data.get('featured_image')
        if image and hasattr(image, 'size'):
            # 1. Size limit: 5MB
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Featured image size cannot exceed 5MB.")
            
            # 2. Extension whitelist (prevent SVG XSS, executable uploads)
            import os
            valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError("Only JPG, JPEG, PNG, or WebP images are allowed.")
            
            # 3. Content verification via PIL
            try:
                from PIL import Image
                img = Image.open(image)
                img.verify()
                if hasattr(image, 'seek'):
                    image.seek(0)
            except Exception:
                raise forms.ValidationError("Uploaded file is corrupt or not a valid image.")

        return image


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Description...'}),
        }


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tag name'}),
        }
