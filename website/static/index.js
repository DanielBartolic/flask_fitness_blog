function loadAllPosts() {
    fetch("/all-posts")
        .then(response => response.text())
        .then(html => {
            document.getElementById("posts").innerHTML = html;
        })
        .catch(error => console.error("Error loading all posts:", error));
}

function filterByTag(tag) {
    fetch(`/api/filter/${tag}`)
        .then(response => response.text())
        .then(html => {
            document.getElementById('posts').innerHTML = html;
        })
        .catch(err => {
            console.error('Failed to fetch posts:', err);
        });
}

function deleteComment(commentId) {
    fetch(`/delete-comment/${commentId}`, {
        method: "DELETE",
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const commentElement = document.getElementById(`comment-${commentId}`);
            if (commentElement) commentElement.remove();
        } else {
            alert(data.error || "Could not delete comment.");
        }
    })
    .catch(() => alert("Could not delete comment."));
}

function submitComment(postId, formElement) {
    const formData = new FormData(formElement);

    fetch(`/create-comment/${postId}`, {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.html) {
            const list = document.querySelector(`#comments-list-${postId}`);
            list.insertAdjacentHTML("afterbegin", data.html);
            formElement.reset();
        } else {
            alert(data.error || "Failed to add comment.");
        }
    })
    .catch(() => alert("Could not post comment."));
    
    return false; // prevent default form submission
}


function like(postId) {

    fetch(`/like-post/${postId}`, { method: "POST" })
    .then(res => res.json())
    .then(data => {
        const likeCount = document.getElementById(`post-likes-count-${postId}`);
        if (likeCount) likeCount.innerHTML = data["likes"] + " likes";

        updateLikeIcon(postId, data["liked"]);
    })
    .catch(() => alert("Could not like the post."));
}

function updateLikeIcon(postId, liked) {
    const likeButton = document.getElementById(`like-button-${postId}`);
    if (!likeButton) return;

    // Find the container element holding this likeButton
    const container = likeButton.closest('[data-has-image]');
    const hasImage = container?.getAttribute('data-has-image') === 'true';

    if (liked) {
        likeButton.src = "/static/icons/heart_full_icon.png";
    } else {
        likeButton.src = hasImage
            ? "/static/icons/heart_empty_white_icon.png"
            : "/static/icons/heart_empty_icon.png";
    }
}

function likeComment(commentId) {
    const likeCount = document.getElementById(`comment-likes-count-${commentId}`);
    const likeButton = document.getElementById(`comment-like-button-${commentId}`);

    fetch(`/like-comment/${commentId}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            likeCount.textContent = data.likes + " likes";
            likeButton.src = data.liked 
                ? "/static/icons/heart_full_icon.png" 
                : "/static/icons/heart_empty_icon.png";
        })
        .catch(e => alert("Could not like the comment."));
}

function loadMoreComments(postId) {
    const comments = document.querySelectorAll(`#comments-list-${postId} .comment`);
    let shown = 0;
  
    comments.forEach(c => {
      if (!c.classList.contains("hidden")) shown++;
    });
  
    const next = shown + 5;
  
    for (let i = 0; i < comments.length; i++) {
      if (i < next) {
        comments[i].classList.remove("hidden");
      }
    }
  
    if (next >= comments.length) {
      const toggle = document.querySelector(`#comments-section-${postId} .comment-load-more`);
      if (toggle) toggle.style.display = "none";
    }
  }

document.addEventListener("DOMContentLoaded", () => {
    const allComments = document.querySelectorAll(".comments-list");

    allComments.forEach(list => {
        const children = list.querySelectorAll(".comment");
        children.forEach((comment, index) => {
            if (index >= 2) {
                comment.classList.add("hidden");
            }
        });
    });
});