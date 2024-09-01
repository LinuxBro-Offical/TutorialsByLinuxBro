from django.utils import timezone
from home.models import Author, Category, SubCategory, Tag, Story, ContentBlock, Response
from django.core.files import File
import requests
from django.contrib.auth.models import User

# Sample data for authors
author_data = [
    {"username": "techguru", "bio": "Tech enthusiast and blogger.", "profile_picture": "https://images.unsplash.com/photo-1542744173-4c3a21b8e945"},
    {"username": "codewizard", "bio": "Passionate about coding and software development.", "profile_picture": "https://images.unsplash.com/photo-1562057412-2591180f557c"},
    {"username": "webmaster", "bio": "Web developer and designer.", "profile_picture": "https://images.unsplash.com/photo-1573164574300-8c0bfcf8f63d"},
    {"username": "datascientist", "bio": "Expert in data analysis and machine learning.", "profile_picture": "https://images.unsplash.com/photo-1506748686214e9df14fedd"},
    {"username": "devopspro", "bio": "DevOps engineer with a focus on automation.", "profile_picture": "https://images.unsplash.com/photo-1555685818-91a8e5360517"},
]

# Create authors
authors = []
for data in author_data:
    user = User.objects.create(username=data["username"], password="password123")  # Replace with appropriate user creation method
    author = Author.objects.create(
        user=user,
        bio=data["bio"],
        profile_picture=File(requests.get(data["profile_picture"], stream=True).raw, name=f"{data['username']}_profile.jpg")
    )
    authors.append(author)

# Sample data for categories and subcategories
category = Category.objects.create(name="Technology", description="Tech-related blog posts")
sub_category = SubCategory.objects.create(category=category, name="Software Development", description="Software development topics")

# Sample data for tags
tags = [
    Tag.objects.create(name="Django"),
    Tag.objects.create(name="Angular"),
    Tag.objects.create(name="React"),
    Tag.objects.create(name="JavaScript"),
    Tag.objects.create(name="CSS"),
]

# Create sample blogs with content blocks
blog_data = [
    {
        "title": "Exploring Django for Web Development",
        "subtitle": "A deep dive into Django framework",
        "cover_image": "https://images.unsplash.com/photo-1562775465-6b5878df85b4",
        "author": authors[0],
        "category": category,
        "sub_category": sub_category,
        "tags": [tags[0]],
        "content_blocks": [
            {"content_type": "paragraph", "text_content": "Django is a powerful framework for building web applications. It follows the model-template-view (MTV) architectural pattern."},
            {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1581093459771-9d02b1788f34"},
            {"content_type": "paragraph", "text_content": "Django comes with a lot of built-in features like authentication, admin interface, and more. It's designed to help developers take applications from concept to completion as swiftly as possible."},
            {"content_type": "blockquote", "text_content": "“The Django framework helps developers by providing a lot of the components necessary to build complex web applications out of the box.”"},
            {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1542744173-4c3a21b8e945"},
            {"content_type": "paragraph", "text_content": "To get started with Django, you'll need Python installed on your machine. Django is also highly customizable, allowing you to tailor the framework to your specific needs."},
        ]
    },
    {
        "title": "Getting Started with Angular",
        "subtitle": "Learn the basics of Angular",
        "cover_image": "https://images.unsplash.com/photo-1573164574300-8c0bfcf8f63d",
        "author": authors[1],
        "category": category,
        "sub_category": sub_category,
        "tags": [tags[1]],
        "content_blocks": [
            {"content_type": "paragraph", "text_content": "Angular is a platform and framework for building single-page client applications using HTML and TypeScript. Developed by Google, Angular provides a comprehensive solution for both the client and server sides."},
            {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1567414310-8dff2b2b03ef"},
            {"content_type": "paragraph", "text_content": "One of the key features of Angular is its use of two-way data binding, which ensures that changes in the model are reflected in the view and vice versa."},
            {"content_type": "blockquote", "text_content": "“Angular’s use of TypeScript helps developers catch errors early and write cleaner code.”"},
            {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1542744173-4c3a21b8e945"},
            {"content_type": "paragraph", "text_content": "With Angular, you can build complex applications with a modular architecture. The Angular CLI makes it easy to generate components, services, and more."},
        ]
    },
    {
        "title": "Mastering React for Modern Web Apps",
        "subtitle": "Why React is the go-to library",
        "cover_image": "https://images.unsplash.com/photo-1593642532973-d31b6557fa68",
        "author": authors[2],
        "category": category,
        "sub_category": sub_category,
        "tags": [tags[2]],
        "content_blocks": [
            {"content_type": "paragraph", "text_content": "React is a JavaScript library for building user interfaces, maintained by Facebook and a community of developers. It allows developers to create large web applications that can change data, without reloading the page."},
            {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1542744173-4c3a21b8e945"},
            {"content_type": "paragraph", "text_content": "React’s component-based architecture allows for reusable and modular code. Components can manage their own state, making it easy to develop complex UIs."},
            {"content_type": "blockquote", "text_content": "“React enables developers to build dynamic and responsive user interfaces with ease.”"},
            {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1560737433-8dff1e14b6ef"},
            {"content_type": "paragraph", "text_content": "React also supports server-side rendering, which can improve the performance and SEO of your web applications."},
        ]
    },
    {
        "title": "The Basics of JavaScript",
        "subtitle": "Understanding JavaScript fundamentals",
        "cover_image": "https://images.unsplash.com/photo-1506748686214-e9df14fedd",
        "author": authors[3],
        "category": category,
        "sub_category": sub_category,
        "tags": [tags[3]],
        "content_blocks": [
            {"content_type": "paragraph", "text_content": "JavaScript is a versatile programming language used primarily for enhancing the interactivity and functionality of web pages. It can be run on the client-side in a browser or server-side with Node.js."},
            {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1506748686214-e9df14fedd"},
            {"content_type": "paragraph", "text_content": "JavaScript supports object-oriented, imperative, and functional programming styles. It is essential for modern web development and integrates seamlessly with HTML and CSS."},
            {"content_type": "blockquote", "text_content": "“JavaScript allows developers to create dynamic and interactive web applications.”"},
            {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1587573910800-5cfd6840e6d8"},
            {"content_type": "paragraph", "text_content": "Learning JavaScript fundamentals is crucial for any web developer. It provides the foundation for understanding more advanced concepts and libraries."},
        ]
    },
    {
        "title": "Styling with CSS",
        "subtitle": "Best practices for CSS",
        "cover_image": "https://images.unsplash.com/photo-1493834027015-c8d54d25f90b",
        "author": authors[4],
        "category": category,
        "sub_category": sub_category,
        "tags": [tags[4]],
        "content_blocks": [
            {"content_type": "paragraph", "text_content": "CSS (Cascading Style Sheets) is used to control the visual appearance of web pages. It allows developers to apply styles to HTML elements and create aesthetically pleasing designs."},
            {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1506748686214-e9df14fedd"},
            {"content_type": "paragraph", "text_content": "CSS supports various properties and selectors to target elements and apply styles. It also allows for responsive design, which ensures that web pages look good on different devices and screen sizes."},
            {"content_type": "blockquote", "text_content": "“CSS provides the means to enhance the visual design and user experience of web pages.”"},
            {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1542744173-4c3a21b8e945"},
            {"content_type": "paragraph", "text_content": "Using CSS preprocessors like SASS or LESS can also streamline your workflow and offer more advanced styling capabilities."},
        ]
    }
]

# Create stories and content blocks
for blog in blog_data:
    story = Story.objects.create(
        title=blog["title"],
        subtitle=blog["subtitle"],
        cover_image=File(requests.get(blog["cover_image"], stream=True).raw, name=f"{blog['title'].replace(' ', '_').lower()}_cover.jpg"),
        author=blog["author"],
        category=blog["category"],
        sub_category=blog["sub_category"],
        publication_date=timezone.now(),
        approval_status='approved',
        views=0
    )
    
    for block in blog["content_blocks"]:
        ContentBlock.objects.create(
            story=story,
            content_type=block["content_type"],
            order=blog["content_blocks"].index(block),
            text_content=block.get("text_content"),
            image_content=File(requests.get(block.get("image_content"), stream=True).raw, name=f"{story.title.replace(' ', '_').lower()}_block_{blog['content_blocks'].index(block)}.jpg") if block.get("image_content") else None,
        )

# Add responses from other authors
responses = [
    {"story": Story.objects.get(title="Exploring Django for Web Development"), "author": authors[1], "liked": True, "comment": "Great insights on Django! The images are also very informative.", "date": timezone.now()},
    {"story": Story.objects.get(title="Getting Started with Angular"), "author": authors[2], "liked": False, "comment": "I found this Angular guide very useful. However, a bit more code examples would be helpful.", "date": timezone.now()},
    {"story": Story.objects.get(title="Mastering React for Modern Web Apps"), "author": authors[3], "liked": True, "comment": "React’s component-based approach is well-explained. The images help a lot to visualize the concepts.", "date": timezone.now()},
    {"story": Story.objects.get(title="The Basics of JavaScript"), "author": authors[4], "liked": False, "comment": "Interesting points on JavaScript. Some advanced topics could be included in future posts.", "date": timezone.now()},
]

# Create responses
for response in responses:
    Response.objects.create(
        story=response["story"],
        author=response["author"],
        liked=response["liked"],
        comment=response["comment"],
        date=response["date"],
    )
