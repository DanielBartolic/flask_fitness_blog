import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, render_template_string
from flask_login import login_required, current_user
from .models import Post, User, Comment, Like, CommentLike
from werkzeug.utils import secure_filename
from . import db

views = Blueprint("views", __name__)


@views.route("/")
@views.route("/home")
def home():
    posts = Post.query.order_by(Post.date_created.desc()).all()
    return render_template("home.html", user=current_user, posts=posts)


@views.route('/make-me-admin')
@login_required
def make_me_admin():
    if current_user.admin:
        return "You're already admin."
    current_user.admin = True
    db.session.commit()
    return "You are now admin!"


@views.route("/all-posts")
def all_posts():
    posts = Post.query.order_by(Post.date_created.desc()).all()
    return render_template("tag_posts.html", posts=posts, user=current_user)

@views.route('/api/filter/<tag>')
def api_filter(tag):
    tag = f'#{tag.lower()}'
    posts = Post.query.filter(Post.text.ilike(f'%{tag}%')).order_by(Post.date_created.desc()).all()
    return render_template('tag_posts.html', posts=posts, user=current_user)

@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    if not current_user.admin:
        return redirect(url_for('views.home'))
    if request.method == "POST":
        text = request.form.get('text')
        file = request.files.get('file_input')
        filename = None

        if file:
            file_ext = os.path.splitext(file.filename)[1]
            filename = f"{current_user.username}_{len(current_user.posts)+1}{file_ext}"
            print(filename)
            upload_path = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_path, exist_ok=True)
            save_path = os.path.join(upload_path, filename)
            print(f"Saving file to: {save_path}") 
            file.save(save_path)

        if not text:
            flash('Post cannot be empty', category='error')
        else:
            post = Post(text=text, image=filename, author=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Post created', category='success')
            return redirect(url_for("views.home"))
    return render_template("create_post.html", user=current_user)

@views.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()
    if not post:
        flash("Post does not exist.", category="error")
    elif current_user.id != post.author:
        flash("You don't have permission to delete this post.", category="error")
    else:
        db.session.delete(post)
        db.session.commit()
        flash("Post deleted.", category="success")
    
    return redirect(url_for("views.home"))



@views.route("/edit-post/<id>", methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category="error")
    elif current_user.id != post.author:
        flash("You don't have permission to edit this post.", category="error")
    else:
        if request.method == "POST":
            text = request.form.get("text")
            if not text: 
                flash("Post cannot be empty.", category="error")
            else:
                post.text=text
                db.session.commit()
                flash("Post updated!", category="success")
                return redirect(url_for("views.home"))
    
    return render_template("edit_post.html", post=post, user=current_user)



@views.route("/delete-comment/<int:comment_id>", methods=["DELETE"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "Comment does not exist."}), 404
    if current_user.id != comment.author and current_user.id != comment.post.author:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(comment)
    db.session.commit()
    return jsonify({"success": True, "comment_id": comment_id})

@views.route("/create-comment/<int:post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get("text", "").strip()
    if not text:
        return jsonify({"error": "Comment can't be empty"}), 400

    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post does not exist"}), 404

    comment = Comment(text=text, author=current_user.id, post_id=post_id)
    db.session.add(comment)
    db.session.commit()

    # Render the new comment HTML with your updated structure
    comment_html = render_template_string("""
<div class="comment" id="comment-{{ comment.id }}" data-index="0">
  <div class="comment-outer">
    <div class="comment-inner1">
      <div class="comment-inner1-1">
        <span class="comment-user">
          <a class="comment-user1" href="/posts/{{ comment.user.username }}">{{ comment.user.username }}</a>:
        </span>

        <span class="comment-text">{{ comment.text }}</span>
        <br>
        <div class="comment-inner1-1-footer">
          <small>
            <span class="comment-likes-count" id="comment-likes-count-{{ comment.id }}">{{ comment.likes|length }} likes</span>, 
            <span class="comment-date">{{ comment.date_created|timeago }}</span>
          </small>
        </div>
      </div>

      <div class="comment-like-controls">
        <img 
          src="{{ url_for('static', filename='icons/' + ('heart_full_icon.png' if user.id in comment.likes|map(attribute='author')|list else 'heart_empty_icon.png')) }}" 
          alt="Like" 
          class="comment-like-button" 
          id="comment-like-button-{{ comment.id }}" 
          onclick="likeComment('{{ comment.id }}')"
        />
      </div>
    </div>

    <div class="comment-inner2">
      {% if user.id == comment.author or user.id == post.author %}
      <img 
        src="{{ url_for('static', filename='icons/trash_icon.png') }}" 
        alt="Delete" 
        class="comment-delete-icon" 
        onclick="deleteComment('{{ comment.id }}')" 
      />
      {% endif %}
    </div>
  </div>
</div>
""", comment=comment, user=current_user, post=post)

    return jsonify({"html": comment_html})

@views.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash("User doesn't exist", category="error")
        return redirect(url_for("views.home"))
    
    posts = user.posts

    return render_template("posts.html", user=current_user, posts=posts, username=username)


@views.route("/like-post/<post_id>", methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first()
    like = Like.query.filter_by(author=current_user.id, post_id=post_id).first()

    if not post:
        return jsonify({'error': 'Post does not exist.'}, 400)
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author, post.likes)})

@views.route("/like-comment/<comment_id>", methods=["POST"])
@login_required
def like_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()
    like = CommentLike.query.filter_by(author=current_user.id, comment_id=comment_id).first()

    if not comment:
        return jsonify({"error": "Comment does not exist."}), 400

    if like:
        db.session.delete(like)
        db.session.commit()
    else:
        new_like = CommentLike(author=current_user.id, comment_id=comment_id)
        db.session.add(new_like)
        db.session.commit()

    return jsonify({
        "likes": len(comment.likes),
        "liked": current_user.id in [l.author for l in comment.likes]
    })