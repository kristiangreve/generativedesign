from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, \
    ResetPasswordRequestForm, ResetPasswordForm, CompanyForm
from app.models import User, Post, Department, Plan
from app.email import send_password_reset_email
import json
from operator import itemgetter
from app.generative import json_departments_from_db, random_design, generate, get_population_from_database, \
initial_generate, select_objects_for_render, evaluate_layout, update_definition, evaluate_pop, initial_generate_weighted,\
initial_generate_flack, generate_flack, generate_weighted
from app.space_planning import get_layout
import statistics
import matplotlib.pyplot as plt
import os

user_selections = []
user_selections_obj = []
user_input_obj = []
user_input_dict_list = []
latest_definition = ''

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = CompanyForm()
    if form.validate_on_submit():
        current_user.length = form.space_length.data
        current_user.width = form.space_width.data
        current_user.username = form.company_name.data
        current_user.number_of_employees = form.number_of_employees.data
        db.session.commit()
        return redirect(url_for('departments'))
    #performance_test_start()
    return render_template('index.html', title='Company information', form=form)


@app.route('/floor_plan', methods=['GET', 'POST'])
@login_required
def floor_plan():
    return render_template('floor_plan.html')

@app.route('/get_floorplans', methods = ['GET','POST'])
@login_required
def get_floorplans():
    global latest_definition
    pop_size = 100
    generations = 50
    mutation_rate = 0.1

    mode = request.form['mode']
    user_groups = json.loads(request.form['user_groups'])
    edges_of_user_groups = json.loads(request.form['edges_of_user_groups'])



    #weights = [5,3,3,3,1,10,0]
    weights = [3,3,3,20,1,3,0]

    #attributes_weight = {'dims_score':weights[0],'access_score':weights[1],'transit_connections_score':weights[2],'adjacency_score':weights[3],'group_adj_score':weights[4],'aspect_ratio_score':weights[5], 'crowding_score':weights[6]}

    definition = update_definition(user_groups)
    print("definition: ", definition)

    if mode == 'restart':
        print("restarting")
        #Pt = initial_generate_flack(pop_size, generations, mutation_rate, definition)
        Pt = initial_generate_weighted(pop_size, generations, mutation_rate, definition,weights)

    else:
        if latest_definition == definition:
            print("defintion did not change")
            #Pt = generate_flack(pop_size, generations, mutation_rate, definition, user_groups, edges_of_user_groups)
            Pt = generate_weighted(pop_size, generations, mutation_rate, definition, user_groups, edges_of_user_groups,weights)
        else:
            print("defintion changed")
            #Pt = initial_generate_flack(pop_size, generations, mutation_rate, definition)
            Pt = initial_generate_weighted(pop_size, generations, mutation_rate, definition,weights)

    # updating the most recent definition

    latest_definition = definition

    return jsonify(select_objects_for_render(Pt, []))

@app.route('/change_transit_of_department', methods = ['GET','POST'])
@login_required
def change_transit_of_department():
    department = request.form['department']
    dep = Department.query.filter_by(name = department).first()
    print(dep.name,dep.transit)
    transit = dep.transit
    if transit == 1:
        transit = 0
    else:
        transit = 1
    dep.transit = transit
    print(dep.name,dep.transit)
    db.session.commit()
    return jsonify(transit)




@app.route('/departments', methods=['GET', 'POST'])
@login_required
def departments():
    number_of_employees = current_user.number_of_employees

    number_of_bathrooms = 0

    # add one bathroom per 10 employees, if 11, 2 is added.
    while(number_of_employees > 0):
        number_of_bathrooms+=1
        number_of_employees-=10

    # suggested bathrooms
    suggested_departments = [{"name": "Bathroom "+str(i),"size":6} for i in range(number_of_bathrooms)]


    departments = Department.query.all()

    window_room = 0
    transit_room = 0

    if request.method == 'POST':
        if request.form.get('action') != 'add':
            print("name of department: ",str(request.form.get('action')))
            name_of_department = str(request.form.get('action')).capitalize()
            dep = Department.query.filter_by(name = name_of_department).first()
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
    return render_template('departments.html', title='Departments', departments=departments, suggested_departments = suggested_departments)

# @app.route('/delete_department/<department>', methods=['GET'])
# @login_required
# def delete_department(department):
#     department = Department.query.filter_by(name = department).first()
#     try:
#         adjacents = json.loads(department.adjacency)
#         for adj in adjacents:
#             dep = Department.query.filter_by(name = adj).first()
#             dep_adjacents = json.loads(dep.adjacency)
#             dep_adjacents.remove(department.name)
#             dep.adjacency = json.dumps(dep_adjacents)
#     except:
#         pass
#     db.session.delete(department)
#     db.session.commit()
#     return redirect(url_for('departments'))

#
# @app.route('/edit_department/<department>', methods=['GET', 'POST'])
# @login_required
# def edit_department(department):
#     departments = current_user.departments
#     department = Department.query.filter_by(name = department).first_or_404()
#     form = EditDepartmentForm()
#     if form.validate_on_submit():
#         department.name = form.name.data.capitalize()
#         department.size = form.size.data
#         department.employees = form.employees.data
#         db.session.commit()
#         return redirect(url_for('departments'))
#     elif request.method == 'GET':
#         form.size.data = department.size
#         form.name.data = department.name.capitalize()
#         form.employees.data = department.employees
#     return render_template('edit_department.html', title='Edit department', form=form, departments=departments)

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
