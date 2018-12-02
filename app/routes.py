from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, \
    ResetPasswordRequestForm, ResetPasswordForm, DepartmentForm, EditDepartmentForm, EditFloorPlanForm
from app.models import User, Post, Department, Plan
from app.email import send_password_reset_email
import json
from operator import itemgetter
from app.generative import json_departments_from_db, random_design, generate, get_population_from_database, \
initial_generate, select_objects_for_render, evaluate_layout, id_to_obj, update_definition
from app.space_planning import get_layout
import statistics
import matplotlib.pyplot as plt
import os

user_selections = []
user_selections_obj = []

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/floor_plan/', methods=['GET', 'POST'])
@login_required
def floor_plan():
    departments = current_user.departments
    return render_template('floor_plan.html',departments=departments)

# AJAX functions
@app.route('/generate_first_floorplans/', methods = ['POST'])
def generate_first_floorplans():
    # generate first generation and return
    pop_size = 4
    generations = 1
    #print("user selections: ",user_selections)
    Pt = initial_generate(pop_size, generations)
    #print("first floorplans rendered")
    return jsonify(select_objects_for_render(Pt, []))

def performance_test(pop,gen,mut):
    global user_selections #If not declared global it doesnt edit the global list but simply creates a local new list with same name
    global user_selections_obj
    user_selections = []
    user_selections_obj = []
    # generate first generation and return
    pop_size = pop
    generations = gen
    mutation_rate = mut
    print("user selections: ",user_selections)
    Pt,plt1,plt2, time = initial_generate(user_selections, pop_size, generations, mutation_rate)
    print("first floorplans rendered")
    #return jsonify(select_objects_for_render(Pt, user_selections))
    return plt1,plt2, time

def performance_test_start():
    pop_size = [25,50,100]
    generations = [25,100,200]
    mut_rate = [0.01, 0.05, 0.1, 0.2]

    for pop in pop_size:
        for gen in generations:
            for mut in mut_rate:
                plt1 = []
                plt2 = []
                time = []
                for i in range(5):
                    plt1_temp,plt2_temp,time_temp = performance_test(pop,gen,mut)
                    plt1.append(plt1_temp[1:])
                    plt2.append(plt2_temp[1:])
                    time.append(round(time_temp,2))
                    plt2x = plt2_temp[0]
                y1_list, y2_list, y3_list = [],[],[]
                for plot_list in plt2:
                    for index, y_lists in enumerate(plot_list):
                        if index == 0:
                            y1_list.append(y_lists)
                        elif index == 1:
                            y2_list.append(y_lists)
                        elif index == 2:
                            y3_list.append(y_lists)
                avg_time = round((sum(time)/len(time)),2)

                y_1_average = [statistics.mean(k) for k in zip(*y1_list)]
                y_2_average = [statistics.mean(k) for k in zip(*y2_list)]
                y_3_average = [statistics.mean(k) for k in zip(*y3_list)]

                stringlabel = 'Avg. Runtime: '+str(avg_time)+' Pop size:'+str(pop)+' #of gen: '+str(gen)+' mutation: '+str(mut)
                stringshort = 'P'+str(pop)+'-G'+str(gen)+'-M'+str(mut)+'_'
                plot_multiple(plt2x, y_1_average,y_2_average,y_3_average,stringlabel, stringshort)

def plot_multiple(x_b,y_b1,y_b2,y_b3,stringlabel,stringshort):
    plt.figure(figsize=(30,15), dpi=80)
    y_plots = [y_b1,y_b2,y_b3]
    labels = ['Avg. #Broken adjacencies','Avg. Aspect ratio deviation','Avg. #Broken min. dimensions']
    colors = ['red','blue','green']
    #plt.plot(x_b, y_b1,'b', x_b, y_b2,'g',  x_b, y_b3, 'r')
    for y_val, label,color in zip(y_plots, labels,colors):
         plt.plot(x_b, y_val, label=label, color=color)
    plt.legend(fontsize=20)
    plt.ylim(0, 10)
    plt.yticks(range(10))
    plt.xlabel('Generation. ('+stringlabel+')',fontsize=15)

    filename = 'photos/avg_BestOf_'+stringshort
    i = 0
    while os.path.exists('{}{:d}.png'.format(filename, i)):
        i += 1
    plt.savefig('{}{:d}.png'.format(filename, i), box_inches='tight')


@app.route('/generate_new_floorplans/', methods = ['GET', 'POST'])
def generate_new_floorplans():
    generations = 10
    selected_rooms = json.loads(request.form['selected_rooms'])
    current_generation = db.session.query(Plan).order_by(Plan.generation.desc()).first().generation
    nodes = json.loads(request.form['nodes'])
    edges = json.loads(request.form['edges'])

    update_definition(edges,nodes,current_generation)

    Pt = get_population_from_database(current_generation)

    if len(selected_rooms)>0:
        user_selections.append(selected_rooms)
        #print("User selection sum: ", user_selections)
        user_selections_obj.append(id_to_obj(Pt,user_selections))
    # create new generation based on choices
    Pt = generate(user_selections_obj,user_selections, generations)
    return jsonify(select_objects_for_render(Pt,user_selections_obj))

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = EditFloorPlanForm()
    if form.validate_on_submit():
        current_user.length = form.length.data
        current_user.width = form.width.data
        db.session.commit()
        return redirect(url_for('departments'))
    #performance_test_start()
    return render_template('index.html', title='Home', form=form)


        # try:
        #     adjacents = json.loads(department.adjacency)
        #     for adj in adjacents:
        #         dep = Department.query.filter_by(name = adj).first()
        #         dep_adjacents = json.loads(dep.adjacency)
        #         dep_adjacents.remove(department.name)
        #         dep.adjacency = json.dumps(dep_adjacents)
        # except:
        #     pass


@app.route('/departments', methods=['GET', 'POST'])
@login_required
def departments():
    departments = current_user.departments

    # print(departments)
    #form = DepartmentForm()
    space_left = current_user.length * current_user.width - sum([dep.size for dep in departments])


    # form code:
    window_room = 0
    transit_room = 0

    if request.method == 'POST':
        if request.form.get('action') != 'add':

            print("name of department: ",str(request.form.get('action')))
            name_of_department = str(request.form.get('action')).capitalize()
            dep = Department.query.filter_by(name = name_of_department).first()
            print(dep)

            db.session.delete(dep)
            db.session.commit()

        if request.form.get('action') == 'add':
            if request.form.get('window_room'):
                window_room = 1
            if request.form.get('transit_room'):
                transit_room = 1
            name_of_department = str(request.form.get('name_of_department')).capitalize()

            if request.form.get('number_of_employees'):
                number_of_employees = int(request.form.get('number_of_employees'))
            else:
                number_of_employees = 0

            # check if an area has been submitted, if not calculate area from number of employees
            if request.form.get('area_of_department'):
                area = int(request.form.get('area_of_department'))
            else:
                area = number_of_employees*7

            dep = Department(name = name_of_department, size = area, employees = number_of_employees, transit = transit_room, window = window_room, owner = current_user)
            db.session.add(dep)
            db.session.commit()

        return redirect(url_for('departments'))

    return render_template('departments.html', title='Departments', departments=departments, space = space_left)



@app.route('/delete_department/<department>', methods=['GET'])
@login_required
def delete_department(department):
    department = Department.query.filter_by(name = department).first()
    try:
        adjacents = json.loads(department.adjacency)
        for adj in adjacents:
            dep = Department.query.filter_by(name = adj).first()
            dep_adjacents = json.loads(dep.adjacency)
            dep_adjacents.remove(department.name)
            dep.adjacency = json.dumps(dep_adjacents)
    except:
        pass
    db.session.delete(department)
    db.session.commit()
    return redirect(url_for('departments'))


@app.route('/edit_department/<department>', methods=['GET', 'POST'])
@login_required
def edit_department(department):
    departments = current_user.departments
    department = Department.query.filter_by(name = department).first_or_404()
    form = EditDepartmentForm()
    if form.validate_on_submit():
        department.name = form.name.data.capitalize()
        department.size = form.size.data
        department.employees = form.employees.data
        db.session.commit()
        return redirect(url_for('departments'))
    elif request.method == 'GET':
        form.size.data = department.size
        form.name.data = department.name.capitalize()
        form.employees.data = department.employees
    return render_template('edit_department.html', title='Edit department', form=form, departments=departments)

@app.route('/adjacency', methods=['GET', 'POST'])
@login_required
def adjacency():
    departments = current_user.departments
    return render_template('adjacency.html', title='adjacency', departments=departments)

@app.context_processor
def utility_processor():
    def adjacent_list_check(department_row,department_col):
        if department_row == current_user.departments[0].name and department_col == current_user.departments[1].name:
            global plotlist
            plotlist = []
        else:
            plotlist.append((department_row,department_col))
        if (department_col,department_row) not in plotlist and department_row != department_col:
            return True
        else:
            return False
    return dict(adjacent_list_check=adjacent_list_check)

@app.template_filter('json_to_list')
def json_to_list(json_obj):
    return json.loads(json_obj)

@app.context_processor
def utility_processor():
    def check_adj(department_row,department_col):
            # retrieve departments from database
            department1 = Department.query.filter_by(name = department_row).first_or_404()
            department2 = Department.query.filter_by(name = department_col).first_or_404()
            # check if they are adjacent
            try:
                adj_1 = json.loads(department1.adjacency)
                if department2.name in adj_1:
                    return True
                else:
                    return False
            except:
                return False
    return dict(check_adj=check_adj)

@app.route('/add_adjacency/<department1>/<department2>', methods=['GET'])
@login_required
def add_adjacency(department1,department2):
    # fetch departments from database
    department1 = Department.query.filter_by(name = department1).first_or_404()
    department2 = Department.query.filter_by(name = department2).first_or_404()
    try:
        adj_1 = json.loads(department1.adjacency)
        adj_2 = json.loads(department2.adjacency)
        if department1.name not in adj_2:
            adj_2.append(department1.name)
        if department2.name not in adj_1:
            adj_1.append(department2.name)
    except:
        adj_1 = [department2.name]
        adj_2 = [department1.name]
    # convert to json and commit
    department1.adjacency = json.dumps(adj_1)
    department2.adjacency = json.dumps(adj_2)

    db.session.commit()
    return redirect(url_for('adjacency'))

@app.route('/del_adjacency/<department1>/<department2>', methods=['GET'])
@login_required
def del_adjacency(department1,department2):
    # fetch departments from database
    department1 = Department.query.filter_by(name = department1).first_or_404()
    department2 = Department.query.filter_by(name = department2).first_or_404()
    # convert from json
    try:
        adj_1 = json.loads(department1.adjacency)
        adj_2 = json.loads(department2.adjacency)
        adj_2.remove(department1.name)
        adj_1.remove(department2.name)
        # convert to json and commit
        department1.adjacency = json.dumps(adj_1)
        department2.adjacency = json.dumps(adj_2)
    except:
        pass

    db.session.commit()
    return redirect(url_for('adjacency'))


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    departments = user.departments
    return render_template('user.html', user=user, departments=departments)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():

        # updating user data
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data

        # addded
        current_user.wid = form.width.data
        current_user.len = form.length.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))
