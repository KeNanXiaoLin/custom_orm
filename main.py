from orm import Model, IntegerField, StringField, BooleanField, DateTimeField, FloatField, Database
from orm.models import model_fields
import datetime


# Define a User model
@model_fields
class User(Model):
    __table__ = 'users'
    id = IntegerField(primary_key=True)
    username = StringField(max_length=50, nullable=False)
    email = StringField(max_length=100, nullable=False)
    password = StringField(max_length=100, nullable=False)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now_add=True)
    balance = FloatField(default=0.0)


# Define a Post model
@model_fields
class Post(Model):
    __table__ = 'posts'
    id = IntegerField(primary_key=True)
    title = StringField(max_length=200, nullable=False)
    content = StringField(max_length=1000, nullable=True)
    author_id = IntegerField(nullable=False)
    is_published = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now_add=True)


# Main example usage
def main():
    # Database connection
    db_url = 'example.db'
    
    # Create tables
    print("Creating tables...")
    with Database(db_url) as db:
        User.create_table(db)
        Post.create_table(db)
    print("Tables created successfully!")
    
    # Create a user
    print("\nCreating a user...")
    user = User(
        username="johndoe",
        email="john@example.com",
        password="secure123",
        balance=100.50
    )
    
    with Database(db_url) as db:
        user.save(db)
    print(f"User created: {user}")
    
    # Create multiple posts
    print("\nCreating posts...")
    posts = [
        Post(title="First Post", content="This is the first post", author_id=user.id, is_published=True),
        Post(title="Second Post", content="This is the second post", author_id=user.id, is_published=False),
        Post(title="Third Post", content="This is the third post", author_id=user.id, is_published=True)
    ]
    
    with Database(db_url) as db:
        for post in posts:
            post.save(db)
            print(f"Post created: {post}")
    
    # Query all users
    print("\nAll users:")
    with Database(db_url) as db:
        all_users = User.select(db).all()
        for u in all_users:
            print(f"- {u.username} ({u.email}) - Balance: {u.balance}")
    
    # Query published posts
    print("\nPublished posts:")
    with Database(db_url) as db:
        published_posts = Post.select(db).filter_by(is_published=True).all()
        for post in published_posts:
            print(f"- {post.title} (Author ID: {post.author_id})")
    
    # Query posts with filter and order by
    print("\nPosts ordered by title (descending):")
    with Database(db_url) as db:
        ordered_posts = Post.select(db).order_by('title', ascending=False).all()
        for post in ordered_posts:
            print(f"- {post.title} (Published: {post.is_published})")
    
    # Update a user's balance
    print("\nUpdating user balance...")
    user.balance += 50.0
    with Database(db_url) as db:
        user.save(db)
    print(f"User updated: {user.username} - New balance: {user.balance}")
    
    # Delete a post
    print("\nDeleting a post...")
    post_to_delete = posts[1]
    with Database(db_url) as db:
        post_to_delete.delete(db)
    print(f"Post deleted: {post_to_delete.title}")
    
    # Count posts
    print("\nCounting posts:")
    with Database(db_url) as db:
        total_posts = Post.select(db).count()
        published_count = Post.select(db).filter_by(is_published=True).count()
        print(f"Total posts: {total_posts}")
        print(f"Published posts: {published_count}")
    
    # Get a specific user
    print("\nGetting a specific user...")
    with Database(db_url) as db:
        retrieved_user = User.get(db, user.id)
        print(f"Retrieved user: {retrieved_user.username}")
    
    # Drop tables (for cleanup)
    print("\nDropping tables...")
    with Database(db_url) as db:
        Post.drop_table(db)
        User.drop_table(db)
    print("Tables dropped successfully!")
    
    print("\nORM example completed!")


if __name__ == "__main__":
    main()
