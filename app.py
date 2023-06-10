from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import requests
import os

CHAT_ID = os.getenv('CHAT_ID')
TOKEN = os.getenv('TOKEN')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    posts = db.relationship('Post', backref='user', lazy=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/', methods=['GET'])
def status():
    return jsonify({'Status': "OKOKOK"}), 200
    
    
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data['name']
    email = data['email']
    password = data['password']
    user = User(name=name, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']
    user = User.query.filter_by(email=email).first()
    if user is None or not user.password == password:
        return jsonify({'message': 'Invalid email or password'}), 401
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}), 200


@app.route('/posts', methods=['GET'])
@jwt_required()
def get_posts():
    posts = Post.query.all()
    return jsonify([{'title': post.title, 'content': post.content} for post in posts]), 200


@app.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    data = request.get_json()
    title = data['title']
    content = data['content']
    user_id = get_jwt_identity()
    post = Post(title=title, content=content, user_id=user_id)
    bot_text = title + "\n" + content + "\n\n" + "@" + User.query.get_or_404(user_id).name
    requests.get('https://api.telegram.org/bot' + TOKEN + '/sendMessage?chat_id=' + CHAT_ID + '&text=' + bot_text)
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Post created'}), 201


@app.route('/posts/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.user_id != get_jwt_identity():
        return jsonify({'message': 'You cannot delete this post'}), 403
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted'}), 200


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
