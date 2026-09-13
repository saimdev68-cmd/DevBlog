import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from PIL import Image, ImageDraw
from apps.blog.models import Category, Tag, Post
from apps.comments.models import Comment

User = get_user_model()


def generate_article_banner(filename, badge_text, title_line1, title_line2, bg_start, bg_end, badge_color):
    """Generates an editorial tech banner image and returns the relative upload path."""
    media_dir = os.path.join(settings.MEDIA_ROOT, 'posts', 'banners')
    os.makedirs(media_dir, exist_ok=True)
    filepath = os.path.join(media_dir, filename)

    width, height = 1200, 630
    img = Image.new('RGB', (width, height), color=bg_start)
    draw = ImageDraw.Draw(img)

    # Vertical gradient background
    for y in range(height):
        ratio = y / height
        r = int(bg_start[0] + (bg_end[0] - bg_start[0]) * ratio)
        g = int(bg_start[1] + (bg_end[1] - bg_start[1]) * ratio)
        b = int(bg_start[2] + (bg_end[2] - bg_start[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Outer decorative border
    draw.rectangle([(40, 40), (width - 40, height - 40)], outline=(255, 255, 255), width=2)
    draw.rectangle([(50, 50), (width - 50, height - 50)], outline=(badge_color[0], badge_color[1], badge_color[2]), width=1)

    # Category Badge Pill
    draw.rectangle([(90, 90), (380, 140)], fill=badge_color)
    draw.text((110, 105), badge_text.upper(), fill=(255, 255, 255))

    # Big Article Title
    draw.text((90, 220), title_line1, fill=(255, 255, 255))
    if title_line2:
        draw.text((90, 280), title_line2, fill=(241, 245, 249))

    # Decorative separator
    draw.line([(90, 480), (450, 480)], fill=(badge_color[0], badge_color[1], badge_color[2]), width=4)

    # Bottom Branding
    draw.text((90, 510), "DEVBLOG  •  PRODUCTION-GRADE ENGINEERING PUBLICATION", fill=(203, 213, 225))

    img.save(filepath, format="PNG")
    return f"posts/banners/{filename}"


class Command(BaseCommand):
    help = "Seed DevBlog with high-quality articles, banner images, categories, and tags"

    def handle(self, *args, **options):
        # 1. Determine Author
        author = User.objects.filter(is_superuser=True).first()
        if not author:
            author, created = User.objects.get_or_create(
                email='admin@devblog.io',
                defaults={
                    'first_name': 'DevBlog',
                    'last_name': 'Editorial',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                author.set_password('admin123456')
                author.save()

        # Update profile bio and avatar with site logo
        if hasattr(author, 'profile'):
            if not author.profile.bio:
                author.profile.bio = "Systems architect and technical writer at DevBlog covering high-scale web architecture."
                author.profile.website = "https://github.com/saimdev68-cmd/DevBlog"
                author.profile.github = "https://github.com/saimdev68-cmd/DevBlog"
            if not author.profile.avatar:
                import shutil
                avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
                os.makedirs(avatars_dir, exist_ok=True)
                src = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
                dst = os.path.join(avatars_dir, 'devblog_logo.png')
                if os.path.exists(src):
                    shutil.copyfile(src, dst)
                    author.profile.avatar = 'avatars/devblog_logo.png'
            author.profile.save()

        # 2. Categories
        cat_django, _ = Category.objects.get_or_create(
            name='Django',
            defaults={'description': 'Deep dives, architectural patterns, and performance tuning with Django.'}
        )
        cat_python, _ = Category.objects.get_or_create(
            name='Python',
            defaults={'description': 'Advanced Python programming techniques, internals, and modern concurrency.'}
        )
        cat_arch, _ = Category.objects.get_or_create(
            name='Architecture',
            defaults={'description': 'System design, database scaling, microservices, and reliable cloud deployments.'}
        )
        cat_web, _ = Category.objects.get_or_create(
            name='Web Development',
            defaults={'description': 'Modern web standards, performance, clean CSS, and accessibility.'}
        )

        # 3. Tags
        tag_orm, _ = Tag.objects.get_or_create(name='ORM')
        tag_django, _ = Tag.objects.get_or_create(name='Django')
        tag_db, _ = Tag.objects.get_or_create(name='Database')
        tag_perf, _ = Tag.objects.get_or_create(name='Performance')
        tag_security, _ = Tag.objects.get_or_create(name='Security')
        tag_async, _ = Tag.objects.get_or_create(name='Async')
        tag_api, _ = Tag.objects.get_or_create(name='API')
        tag_arch, _ = Tag.objects.get_or_create(name='Architecture')
        tag_frontend, _ = Tag.objects.get_or_create(name='Frontend')

        # 4. Generate Images & Articles
        articles_data = [
            {
                'title': 'Optimizing Django ORM Queries: Zero N+1 and Beyond',
                'category': cat_django,
                'tags': [tag_orm, tag_db, tag_perf],
                'is_featured': True,
                'views': 254,
                'banner': ('banner_django_orm.png', 'Django 6 & ORM', 'Optimizing Django ORM Queries:', 'Zero N+1, Prefetching & Beyond', (30, 27, 75), (79, 70, 229), (99, 102, 241)),
                'excerpt': 'Learn how to master select_related, prefetch_related, and database indexes to eliminate latency in production Django apps.',
                'content': """When building enterprise applications with Django, the Object-Relational Mapper (ORM) is one of the framework's greatest assets. However, without careful query design, ORM queries can quietly introduce severe performance bottlenecks, particularly the notorious N+1 query problem.

## The Cost of the N+1 Query

The N+1 problem occurs when an application executes 1 initial query to retrieve a parent list of objects, followed by N subsequent queries to fetch related items for each individual parent.

Consider a simple blog feed:
```python
# Problematic Query (Causes N+1)
posts = Post.objects.filter(status='PUBLISHED')
for post in posts:
    print(post.author.email)  # Triggers an SQL query for EVERY single iteration!
```

If you render 20 posts per page, your database handles 21 independent queries. Under heavy traffic, this exhausts connection pools and destroys response times.

## The Solution: Eager Loading

Django provides two native ORM methods to solve this elegantly:

### 1. `select_related` (SQL JOIN)
For single-valued relationships (`ForeignKey` and `OneToOneField`), `select_related` executes an SQL `JOIN` in the initial query:

```python
posts = Post.objects.select_related('author', 'category').filter(status='PUBLISHED')
```

### 2. `prefetch_related` (SQL IN)
For multi-valued relationships (`ManyToManyField` and reverse ForeignKeys), `prefetch_related` fetches related objects using a separate `WHERE IN` query and matches them in Python memory:

```python
posts = Post.objects.prefetch_related('tags').filter(status='PUBLISHED')
```

## Adding Strategic Indexes

Queries with high cardinality lookups must have corresponding database indexes:

```python
class Post(models.Model):
    status = models.CharField(max_length=15, db_index=True)
    published_at = models.DateTimeField(db_index=True)
```

By profiling queries with tools like `django-debug-toolbar` and ensuring all list views use proactive prefetching, you can keep your server response times under 50 milliseconds even at scale.
"""
            },
            {
                'title': 'Building High-Concurrency Async Services in Python 3.14',
                'category': cat_python,
                'tags': [tag_async, tag_perf],
                'is_featured': False,
                'views': 188,
                'banner': ('banner_async_python.png', 'Python Concurrency', 'Building High-Concurrency Async Services', 'in Modern Python 3.14', (6, 78, 59), (5, 150, 105), (16, 185, 129)),
                'excerpt': 'A deep dive into asyncio task groups, structured concurrency, and event loop optimization for modern Python backends.',
                'content': """Python's asynchronous programming model has matured into a formidable tool for building high-throughput I/O bound services. With recent Python releases, structured concurrency via TaskGroups provides bulletproof error propagation and resource cleanup.

## Why Structured Concurrency Matters

Previous approaches using `asyncio.gather` or fire-and-forget tasks frequently leaked unhandled exceptions or background coroutines when failures occurred midway.

Structured concurrency ensures that child tasks are strictly bounded by the lifetime of their parent scope:

```python
import asyncio

async def fetch_metrics(service_id: int):
    # Simulated network latency
    await asyncio.sleep(0.1)
    return {"id": service_id, "latency_ms": 42}

async def aggregate_services():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_metrics(1))
        task2 = tg.create_task(fetch_metrics(2))
        task3 = tg.create_task(fetch_metrics(3))

    # All tasks are guaranteed complete or cancelled cleanly here
    results = [task1.result(), task2.result(), task3.result()]
    return results
```

If `task2` raises an exception, the remaining tasks in the group are immediately cancelled, preventing orphan operations from consuming CPU and memory.
"""
            },
            {
                'title': 'PostgreSQL Indexing Strategies for Large Scale Backends',
                'category': cat_arch,
                'tags': [tag_db, tag_perf],
                'is_featured': False,
                'views': 142,
                'banner': ('banner_postgres.png', 'Database Architecture', 'PostgreSQL Indexing Strategies', 'Every Senior Backend Engineer Needs', (15, 23, 42), (2, 132, 199), (14, 165, 233)),
                'excerpt': 'Compare B-Tree, GIN, and Partial Indexes in PostgreSQL to accelerate queries and reduce table write overhead.',
                'content': """Indexes are the foundation of database performance. However, blindly indexing columns without understanding how the Postgres query planner evaluates execution trees leads to wasted storage and degraded write throughput.

## When to Use Partial Indexes

One of PostgreSQL's most powerful capabilities is indexing a subset of rows using a `WHERE` clause:

```sql
CREATE INDEX idx_active_posts ON blog_post (published_at DESC)
WHERE status = 'PUBLISHED';
```

In an editorial platform where only published posts are queried publicly, this partial index:
- Occupies a fraction of disk space compared to indexing the entire table.
- Speeds up scans because the working set fits comfortably in RAM.
- Does not require index maintenance when draft articles are edited.

## Multi-Column Indexes and Column Order

In compound indexes `(category_id, published_at)`, column order dictates usability. Postgres can use this index for lookups on `category_id` alone, or `category_id` AND `published_at`, but NOT `published_at` alone. Always order columns by equality filters first, then range filters.
"""
            },
            {
                'title': 'Why Vanilla CSS and HTML Outlive Frontend Frameworks',
                'category': cat_web,
                'tags': [tag_frontend, tag_perf],
                'is_featured': False,
                'views': 115,
                'banner': ('banner_vanilla_web.png', 'Modern Web Standards', 'Why Vanilla CSS & HTML Outlive', 'Heavy JavaScript Frameworks', (67, 20, 7), (234, 88, 12), (249, 115, 22)),
                'excerpt': 'Exploring the enduring advantages of server-rendered HTML, native CSS custom properties, and minimal vanilla JavaScript.',
                'content': """The modern web development landscape has spent the past decade pursuing increasingly complex client-side Single Page Application (SPA) architectures. However, for content-focused platforms and editorial publications, the traditional server-rendered web delivers unmatched speed, reliability, and accessibility.

## The Power of Modern CSS Custom Properties

CSS has evolved dramatically. Features that previously required Sass, Less, or heavy CSS-in-JS runtimes are now natively supported in every modern browser:

```css
:root {
    --color-primary: #4F46E5;
    --font-sans: 'Inter', system-ui, sans-serif;
    --radius-md: 10px;
    --shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.06);
}
```

## Zero-Bundle JavaScript

By leveraging semantic HTML5 and vanilla JavaScript only where interaction genuinely enhances user experience (such as mobile menus and clipboard copying), page load times drop to near zero and bundle parsing overhead disappears entirely.
"""
            },
            {
                'title': 'Hardening Django Security for Production Deployments',
                'category': cat_arch,
                'tags': [tag_security, tag_django],
                'is_featured': False,
                'views': 96,
                'banner': ('banner_security.png', 'Security & Hardening', 'Hardening Django Security', 'for Production Deployments', (46, 16, 101), (124, 58, 237), (167, 139, 250)),
                'excerpt': 'A comprehensive security checklist covering HTTPS enforcement, HSTS headers, secure session cookies, and WhiteNoise.',
                'content': """Security is not a feature you add at the end of development; it is a discipline built into every layer of your Django project.

## Essential Production Security Checklist

When preparing for a public release on Render or cloud hosts, verify that these settings are active whenever `DEBUG=False`:

```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

Always use environment variables for sensitive secrets and ensure `.env` is permanently excluded from version control.
"""
            },
            {
                'title': 'Architecting Scalable REST & RPC APIs for Modern Microservices',
                'category': cat_web,
                'tags': [tag_api, tag_arch],
                'is_featured': False,
                'views': 130,
                'banner': ('banner_api_design.png', 'API Engineering', 'Architecting Scalable REST & RPC APIs', 'for Distributed Systems', (19, 78, 74), (13, 148, 136), (45, 212, 191)),
                'excerpt': 'Guidelines for idempotent endpoints, pagination patterns, API versioning, and rate limiting in modern web services.',
                'content': """A well-designed API is intuitive for clients to consume and resilient under unpredictable load spikes.

## Designing for Idempotency

Network failures are inevitable. Clients will retry requests when they fail to receive an acknowledgement. For state-modifying operations (such as payments or post creation), support `Idempotency-Key` headers:

- Store the processed key with the cached response in Redis.
- If a duplicate key arrives within 24 hours, return the cached result without re-executing business logic.

## Cursor-Based Pagination vs Offset

For large datasets, offset pagination (`OFFSET 5000 LIMIT 20`) forces the database to scan and discard 5,000 rows. Cursor-based pagination uses an indexed timestamp or ID:

```sql
SELECT * FROM posts WHERE id < 1042 ORDER BY id DESC LIMIT 20;
```
This executes an instantaneous index seek regardless of table depth.
"""
            }
        ]

        created_count = 0
        for data in articles_data:
            banner_info = data['banner']
            image_rel_path = generate_article_banner(
                filename=banner_info[0],
                badge_text=banner_info[1],
                title_line1=banner_info[2],
                title_line2=banner_info[3],
                bg_start=banner_info[4],
                bg_end=banner_info[5],
                badge_color=banner_info[6],
            )

            post, created = Post.objects.get_or_create(
                title=data['title'],
                defaults={
                    'author': author,
                    'category': data['category'],
                    'excerpt': data['excerpt'],
                    'content': data['content'].strip(),
                    'featured_image': image_rel_path,
                    'status': 'PUBLISHED',
                    'is_featured': data['is_featured'],
                    'published_at': timezone.now(),
                    'views': data['views'],
                }
            )

            # If post already existed, make sure featured_image is populated
            if not post.featured_image:
                post.featured_image = image_rel_path
                post.save()

            post.tags.set(data['tags'])
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded articles! Created: {created_count}, Total available: {Post.objects.count()}"
            )
        )
