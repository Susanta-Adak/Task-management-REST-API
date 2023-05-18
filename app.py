from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity



app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_manager.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'password': self.password}

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    due_date = db.Column(db.String(20))
    status = db.Column(db.String(30))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'description': self.description, 'due_date': self.due_date, 'status':self.status, 'user_id':self.user_id}

db.create_all()

engine = create_engine('sqlite:///task_manager.db')
Session = sessionmaker(bind=engine)
session = Session()

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')

    user = User.query.filter_by(name=name).first()
    if user:
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(name=name, password=password)
    session.add(new_user)
    session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# user login
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')

    user = User.query.filter_by(name=name, password=password).first()
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401
    user = user.to_dict()
    token = create_access_token(identity=name)
    return jsonify({'message': 'Login successful', 'token': token}), 200


#----TASK----
# creating a task
@app.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    due_date = data.get('due_date')
    status = data.get('status')
    user_name = get_jwt_identity()
    user = User.query.filter_by(name=user_name).first().to_dict()
    user_id = user.get('id')

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User does not exist'}), 404

    new_task = Task(title=title, description=description, due_date=due_date, status=status, user_id=user_id)
    session.add(new_task)
    session.commit()

    return jsonify({'message': 'Task created successfully'}), 201


# get all task by user
@app.route("/tasks/user/", methods=['GET'])
@jwt_required()
def get_task_by_user_id():
    user_name = get_jwt_identity()
    user = User.query.filter_by(name=user_name).first().to_dict()
    if not user:
        return jsonify({'message': 'User does not exist'}), 404
    tasks = Task.query.filter_by(user_id=user.get('id'))
    task_list = [t.to_dict() for t in tasks]
    return jsonify(task_list), 200

# update task
@app.route("/task/<task_id>", methods=['PUT'])
def update_task_by_task_id(task_id):
    data = request.get_json()
    status = data.get('status')
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    task.status = status
    session.commit()
    return jsonify(task.to_dict()), 200

# delete task by id
@app.route("/task/<task_id>", methods=['DELETE'])
def delete_task_by_id(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
    Task.query.filter_by(id = task_id).delete()
    session.commit()
    return jsonify({"message":"Deleted ", "task": task.to_dict()}), 202


#--TEST
# get a task by ID
@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    return jsonify(task.to_dict()), 200

# get all task
@app.route("/tasks", methods=['GET'])
def get_all_task():
    tasks = Task.query.all()
    task_list = [t.to_dict() for t in tasks]
    return jsonify(task_list), 200

# get all user
@app.route("/users", methods=['GET'])
def get_all_user():
    users = User.query.all()
    user_list = [u.to_dict() for u in users]
    return jsonify(user_list), 200