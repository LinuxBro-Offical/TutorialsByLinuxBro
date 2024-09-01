from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files import File
import requests

from home.models import Author, Category, SubCategory, Tag, Story, ContentBlock, Response
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Populate the database with sample blog data'

    def handle(self, *args, **kwargs):
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
            Tag.objects.create(name="HTML"),
            Tag.objects.create(name="Bootstrap"),
            Tag.objects.create(name="jQuery"),
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
                "subtitle": "Building dynamic web applications with Angular",
                "cover_image": "https://images.unsplash.com/photo-1562057412-2591180f557c",
                "author": authors[1],
                "category": category,
                "sub_category": sub_category,
                "tags": [tags[1]],
                "content_blocks": [
                    {"content_type": "paragraph", "text_content": "Angular is a platform for building mobile and desktop web applications. It provides a comprehensive solution with powerful tools and libraries."},
                    {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1603921788782-fd5949d9eaf3"},
                    {"content_type": "paragraph", "text_content": "Angular uses TypeScript for development, offering a strongly typed language that helps prevent many common programming errors."},
                    {"content_type": "blockquote", "text_content": "“Angular is a powerful framework for building scalable and maintainable applications.”"},
                    {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1573164574300-8c0bfcf8f63d"},
                    {"content_type": "paragraph", "text_content": "Getting started with Angular involves setting up a development environment, learning the core concepts, and then diving into building applications."},
                ]
            },
            {
                "title": "Mastering React for Modern Web Apps",
                "subtitle": "A guide to building interactive user interfaces with React",
                "cover_image": "https://images.unsplash.com/photo-1600990937938-31a22f6018d2",
                "author": authors[2],
                "category": category,
                "sub_category": sub_category,
                "tags": [tags[2]],
                "content_blocks": [
                    {"content_type": "paragraph", "text_content": "React is a popular library for building user interfaces, particularly for single-page applications. It helps manage the view layer of web applications."},
                    {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1600990937938-31a22f6018d2"},
                    {"content_type": "paragraph", "text_content": "React's component-based architecture allows developers to create reusable UI components, which makes building and maintaining large applications more manageable."},
                    {"content_type": "blockquote", "text_content": "“React is not just a library, but a whole ecosystem of tools and libraries for building modern web applications.”"},
                    {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1555685818-91a8e5360517"},
                    {"content_type": "paragraph", "text_content": "To master React, it's essential to understand components, state management, and the React lifecycle methods."},
                ]
            },
            {
                "title": "The Basics of JavaScript",
                "subtitle": "Understanding the core concepts of JavaScript",
                "cover_image": "https://images.unsplash.com/photo-1506748686214e9df14fedd",
                "author": authors[3],
                "category": category,
                "sub_category": sub_category,
                "tags": [tags[3]],
                "content_blocks": [
                    {"content_type": "paragraph", "text_content": "JavaScript is a versatile scripting language that runs in the browser. It allows developers to create dynamic and interactive web applications."},
                    {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1506748686214e9df14fedd"},
                    {"content_type": "paragraph", "text_content": "JavaScript is essential for web development, enabling functionalities such as form validation, animations, and handling user interactions."},
                    {"content_type": "blockquote", "text_content": "“JavaScript is a powerful language that brings life to web pages through dynamic features and interactive elements.”"},
                    {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1560807707-8cc77767d783"},
                    {"content_type": "paragraph", "text_content": "Learning JavaScript involves understanding its syntax, data types, functions, and how it integrates with HTML and CSS."},
                ]
            },
            {
                "title": "Introduction to CSS Grid Layout",
                "subtitle": "Building responsive layouts with CSS Grid",
                "cover_image": "https://images.unsplash.com/photo-1563244288-32b8b746d5e1",
                "author": authors[4],
                "category": category,
                "sub_category": sub_category,
                "tags": [tags[4]],
                "content_blocks": [
                    {"content_type": "paragraph", "text_content": "CSS Grid Layout is a powerful layout system available in CSS. It allows developers to create complex and responsive grid-based layouts with ease."},
                    {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1563244288-32b8b746d5e1"},
                    {"content_type": "paragraph", "text_content": "CSS Grid provides a two-dimensional grid system that allows for precise control over the placement of elements, both horizontally and vertically."},
                    {"content_type": "blockquote", "text_content": "“CSS Grid Layout offers a robust solution for creating flexible and responsive web layouts.”"},
                    {"content_type": "image", "image_content": "https://images.unsplash.com/photo-1600990937938-31a22f6018d2"},
                    {"content_type": "paragraph", "text_content": "To get started with CSS Grid, you'll need to understand the basic concepts of grid containers and grid items, as well as how to use grid lines and areas effectively."},
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
            {"story": Story.objects.get(title="Introduction to CSS Grid Layout"), "author": authors[0], "liked": True, "comment": "CSS Grid is a game-changer for responsive design. The practical examples were very useful.", "date": timezone.now()},
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

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with sample data'))
