from flask import Flask, render_template, request, flash, redirect, url_for
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
    name = db.Column(db.String(255), nullable=False, unique=True)
    script = db.Column(db.Text, nullable=True)
    ui_script = db.Column(db.Text, nullable=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    tool_instances = db.relationship('Tool_Instance', back_populates='project')

class Tool_Instance(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tool.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    data = db.Column(db.JSON, nullable=True)  # Store instance-specific data as JSON
    rect = db.Column(db.JSON, nullable=False) # {'x': 2, 'y': 2, 'w': 5, 'h': 5}

    tool = db.relationship('Tool')
    project = db.relationship('Project', back_populates='tool_instances')

    def to_json(self):
        return {
            'id': self.id,
            'tool_id': self.tool_id,
            'name': self.tool.name,
            'project_id': self.project_id,
            'data': self.data,
            'rect': self.rect
        }


@app.route('/')
def home():
    projects = Project.query.all()
    return render_template('home.html', projects=projects)

@app.route('/create_tool', methods=['GET', 'POST'])
def create_tool():
    if request.method == 'POST':
        new_tool = Tool(name=request.form['name'], script=request.form['script'], ui_script=request.form['ui_script'])

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
        tools_list = request.form.get('tools')
        tools_list = json.loads(tools_list)

        if tools_list == []:
            flash('Try Adding a tool :)')
            return redirect(url_for('create_project'))
        
        new_project = Project(name=request.form['name'])
        db.session.add(new_project)
        db.session.commit()

        for tool in tools_list:
            new_tool_instance = Tool_Instance(
                tool_id = int(tool['id']),
                project_id = new_project.id,
                data = {},
                rect = {k: int(tool.get(k, 2)) for k in ['x', 'y', 'w', 'h']}
            )
            db.session.add(new_tool_instance)

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
    tool_instances = [instance.to_json() for instance in Project.query.get_or_404(project_id).tool_instances]

    return render_template('/project.html', tool_instances=tool_instances, project_id=project_id)

@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    if request.method == 'POST':
        tools_list = request.form.get('tools')
        tools_list = json.loads(tools_list)

        for tool in tools_list:
            Tool_Instance.query.get_or_404(tool['id']).rect = tool['rect']
            db.session.commit()

    tool_instances = [instance.to_json() for instance in Project.query.get_or_404(project_id).tool_instances]

    return render_template('/edit_project.html', tool_instances=tool_instances, project_id=project_id)

@app.route('/delete_project/<int:project_id>', methods=['GET', 'POST'])
def delete_project(project_id):
    project = Project.query.get(project_id)
    if request.method == 'POST':
        if project:
            for tool_instance in project.tool_instances:
                db.session.delete(tool_instance)
                db.session.commit()
            db.session.delete(project)
            db.session.commit()
            flash('Project deleted successfully!', 'success')
        else:
            flash('Project not found.', 'danger')
        return redirect(url_for('home'))

    return render_template('delete_project.html', project=project)

if __name__ == '__main__':
    app.run(debug=True)
