from flask import Flask, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import json

app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'key0123456789'


# Initialize the database and migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tools = db.Column(db.JSON, nullable=False)

@app.route('/')
def home():
    projects = Project.query.all()
    return render_template('home.html', projects=projects)

@app.route('/create_tool', methods=['GET', 'POST'])
def create_tool():
    if request.method == 'POST':
        new_tool = Tool(name=request.form['name'])

        try:
            db.session.add(new_tool)
            db.session.commit()
            flash('Tool created successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error creating tool: ' + str(e), 'danger')

    tools = Tool.query.all()
    return render_template('create_tool.html', tools=tools)

@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if request.method == 'POST':
        tools_json = request.form.get('tools')
        tools_list = json.loads(tools_json)
        tools_list = [{k: int(v) if k != 'tool_name' else v for k, v in tool_dict.items()} for tool_dict in tools_list]

        new_project = Project(tools=tools_list)

        if tools_list == []:
            new_project = None

        try:
            db.session.add(new_project)
            db.session.commit()
            flash('Project created successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error creating project: ' + str(e), 'danger')

    tools = Tool.query.all()
    projects = Project.query.all()
    return render_template('create_project.html', tools=tools, projects=projects)

@app.route('/project/<int:project_id>')
def project(project_id):
    tools = Project.query.get_or_404(project_id).tools
    print(tools)

    return render_template('/project.html', tools=tools)

if __name__ == '__main__':
    app.run(debug=True)
