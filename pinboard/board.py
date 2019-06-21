from flask import Blueprint, render_template, request, redirect, url_for, make_response
from pinboard.db import get_db
from datetime import datetime
import time
import json
import random
import math

bp = Blueprint("board", __name__)

@bp.route("/")
def list():
    posts = get_posts(get_cookie(), True)
    response = make_response(render_template("board/list.html", posts=posts, session=get_cookie()))

    if (get_cookie() == ""):
        response.set_cookie("pinboard", generate_random_cookie_hash())
    
    return response

@bp.route("/add", methods=("GET", "POST"))
def add():
    if request.method == "GET":
        return render_template("board/add.html")
    else:
        title = request.form["title"]
        description = request.form["description"]
        color = request.form["color"]

        db = get_db()
        db.execute(
            "INSERT INTO post (title, description, color) VALUES (?, ?, ?)",
            (title, description, color)
        )

        db.commit()

        return redirect(url_for("board.list"))

@bp.route("/like", methods=("GET", "POST"))
def like():
    if request.method == "POST":
        session_post_user = request.form["session_post_user"]
        post_id = request.form["post_id"]

        db = get_db()
        db.execute(
            "INSERT INTO post_likes (session_post_user, post_id) VALUES (?, ?)",
            (session_post_user, post_id)
        )

        db.commit()
        return redirect("/")

def db_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_cookie():
    user_session_cookie = ""
    if 'pinboard' in request.cookies:
        user_session_cookie = request.cookies["pinboard"]

    return user_session_cookie

def generate_random_cookie_hash(length = 10):
    chars = "abcdefghijklmnopqrstuvwxyz1234567890"
    char_length = len(chars)
    hash_cookie = ""
    for c in range(length):
        rand = random.randint(0, char_length - 1)
        hash_cookie += chars[rand]

    return hash_cookie

def get_posts(session, to_json = False):
    db = get_db()

    if to_json:
        db.row_factory = db_factory

    cursor = db.cursor()

    query = """SELECT rowid, *, 
            (SELECT COUNT(*) from post_likes WHERE post_id=post.rowid) as likes, 
            (SELECT COUNT(*) from post_likes WHERE post_id=post.rowid AND session_post_user='{0}') as my_likes 
        FROM post ORDER BY created DESC"""
    rows = cursor.execute(query.format(session)).fetchall()

    sorting = sort_posts(rows)
    return sorting

def sort_posts(posts):
    if len(posts) > 0:
        date_format = "%Y-%m-%d %H:%M:%S"
        for post in posts:
            post_day = post["created"]
            post_day_timestamp = int(datetime.strptime(post_day, date_format).timestamp()) * 1000
            actual_day_timestamp = int(round(time.time() * 1000))

            sqrt_diff = int(math.sqrt(actual_day_timestamp - post_day_timestamp)) + 1
            score = (1 / sqrt_diff) * post["likes"] + 1

            post["like_score"] = score

        sorted_posts = sorted(posts, key=lambda post: post["like_score"], reverse=True)
        return sorted_posts

    else:
        return posts