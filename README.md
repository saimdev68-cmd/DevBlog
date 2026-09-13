# DevBlog — Production-Grade Developer Publication

DevBlog is a modern, production-quality blogging platform built with **Python & Django**. Designed specifically for software engineers, technical writers, and engineering teams, DevBlog feels like a high-end SaaS product rather than a generic blogging site.

---

## 🌟 Key Features

### 1. Public Editorial Experience
- **SaaS + Editorial Aesthetic**: Clean, modern typography (Inter font stack), light neutral palette (`#F8FAFC`, `#0F172A`, `#4F46E5`), and spacious layout.
- **Hero & Curated Showcase**: Large featured publication, dynamic latest article grid (3-cols desktop, 2-cols tablet, 1-col mobile), and popular topic pills.
- **Long-Form Reading Optimization**: Comfortable line length, dark syntax-styled code blocks with horizontal scroll, blockquotes, and headings.
- **Reading Time Estimation**: Dynamic calculation based on article word count (200 words/min).
- **Session-Protected View Counter**: Prevents refresh abuse via session tracking.
- **Reader Discussions**: Moderated comment system where author comments are instant and reader comments await approval.
- **Social Sharing**: Fast, native social share links (X/Twitter, LinkedIn, Facebook) and a one-click "Copy Link" utility with visual feedback.
- **Related Articles**: Intelligently recommends 3 publications based on matching categories and shared tags.

### 2. Author Dashboard (SaaS Admin Studio)
- **Overview Analytics**: Real-time stats for Total Articles, Published, Drafts, Total Views, Comments, and Pending Moderation.
- **Article Lifecycle CRUD**: Full Create, Edit, Delete (with POST confirmation guard), and quick Publish/Unpublish toggle.
- **Category & Tag Management**: Create and inspect topic groupings and publication distribution.
- **Discussion Moderation**: Approve or delete reader comments.
- **Profile Management**: Update author bio, avatar, and social presence.

### 3. Identity & Authentication
- **Email-Based Authentication**: Custom `User` model using email as the unique identifier (no usernames required).
- **Author Profiles**: One-to-one `Profile` model with automatic creation via `post_save` signals.
- **Public Author Profiles**: Dedicated page showcasing author bio, links, and published articles archive.
- **Password Recovery**: Complete password reset workflow with secure Django tokens.

### 4. SEO & Syndication
- **SEO-Friendly URLs**: Automatic slug generation from titles (`/blog/<slug>/`).
- **Rich Meta Tags & Open Graph**: Dynamic OG and Twitter card tags on every article.
- **XML Sitemaps**: Dynamic `/sitemap.xml` indexing articles, categories, and static pages.
- **Search Engine Directives**: Standardized `/robots.txt` disallowing dashboard and admin paths.
- **RSS Feed**: Syndicated `/feed/` providing standard RSS 2.0 XML.

### 5. Frontend Philosophy
- **Zero Frontend Frameworks**: Strictly built using standard **Django Templates + HTML5 + modern CSS3 + Vanilla JavaScript**.
- **No Tailwind, Bootstrap, or SPAs**: Clean custom properties, responsive CSS grid/flexbox, and lightweight vanilla JS enhancements.

---

## 🏗️ Project Architecture

```
devblog/
│
├── manage.py
│
├── config/
│   ├── __init__.py
│   ├── settings.py          # Production-ready settings (WhiteNoise, env, security)
│   ├── urls.py              # Root routing, feeds, and sitemaps
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── core/                # Home, About, Contact, robots.txt
│   ├── accounts/            # Custom User model, Profile, auth views
│   ├── blog/                # Category, Tag, Post models, search, RSS feed
│   ├── comments/            # Moderated Comment system
│   └── dashboard/           # SaaS Author Studio & post management
│
├── templates/
│   ├── base.html            # Main HTML document with SEO meta blocks
│   ├── 404.html, 403.html, 500.html
│   ├── partials/            # navbar, footer, messages, pagination, post_card, empty_state
│   ├── core/
│   ├── accounts/
│   ├── blog/
│   └── dashboard/
│
├── static/
│   ├── css/                 # style.css, components.css, dashboard.css
│   ├── js/                  # main.js, dashboard.js
│   └── images/              # og-default.png
│
├── media/                   # User uploads (posts/, avatars/)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start (Development)

### 1. Clone the repository
```bash
git clone https://github.com/saimdev68-cmd/DevBlog.git
cd DevBlog
```

### 2. Set up virtual environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file based on `.env.example`:
```ini
SECRET_KEY=your-secure-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

### 5. Apply database migrations
```bash
python manage.py migrate
```

### 6. Create a superuser / author
```bash
python manage.py createsuperuser
```

### 7. Run the development server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000` in your browser.

---

## 🧪 Running Automated Tests

DevBlog includes a comprehensive automated test suite testing models, views, query optimization, authentication, comments moderation, and the dashboard.

Run tests:
```bash
python manage.py test
```

---

## 🌐 Production Deployment on Render

### Render Configuration
When deploying to **Render (Web Service)**:

1. **Build Command**:
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python manage.py create_admin
   ```
2. **Start Command**:
   ```bash
   gunicorn config.wsgi:application
   ```

### Environment Variables on Render
Set these in **Render Dashboard &rarr; DevBlog Web Service &rarr; Environment &rarr; Add Environment Variable**:

| Variable | Description | Example / Recommended |
| :--- | :--- | :--- |
| `SECRET_KEY` | Strong random secret key | *(generate random 50+ chars)* |
| `DEBUG` | Disable debug mode in production | `False` |
| `ALLOWED_HOSTS` | Allowed domain names | `.onrender.com,127.0.0.1,localhost` |
| `DJANGO_SUPERUSER_EMAIL` | Admin login email | `admin@yourdomain.com` |
| `DJANGO_SUPERUSER_PASSWORD` | Admin login password | `your-secure-admin-password` |
| `DJANGO_SUPERUSER_FIRST_NAME` | *(Optional)* First name | `Admin` |
| `DJANGO_SUPERUSER_LAST_NAME` | *(Optional)* Last name | `User` |

### How `create_admin` Works:
- **First Deployment**: Creates the initial superuser account safely using the provided environment variables with standard Django password hashing.
- **Subsequent Deployments**: Idempotent. Detects that the superuser already exists and skips creation without altering permissions or overwriting the existing password.


---

## 📄 License
This project is open source and available under the [MIT License](LICENSE).
