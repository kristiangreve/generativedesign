from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, IntegerField, RadioField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired()])
    submit = SubmitField('Submit')


class CompanyForm(FlaskForm):
    company_name = TextAreaField('company_name', validators=[Length(min=0, max=140)], render_kw={"placeholder": "Name of your company"})
    number_of_employees = IntegerField('number_of_employees', validators=[DataRequired()],render_kw={"placeholder": "Number of employees"})



class DepartmentForm(FlaskForm):
    name = TextAreaField('Department', validators=[Length(min=0, max=140)], render_kw={"placeholder": "Name"})
    employees = IntegerField('Employees',render_kw={"placeholder": "#"})
    window = RadioField('Gender', choices = [('M','Male'),('F','Female')])

    transit = BooleanField()
    area = IntegerField('Area', validators=[DataRequired()],render_kw={"placeholder": "m^2"})

    submit = SubmitField('Add')

class EditDepartmentForm(FlaskForm):
    name = TextAreaField('Department name', validators=[Length(min=0, max=140)])
    size = IntegerField('Size', validators=[DataRequired()])
    employees = IntegerField('Number of employees')
    submit = SubmitField('Commit changes')

class EditFloorPlanForm(FlaskForm):
    length = IntegerField('Length', validators=[DataRequired()])
    width = IntegerField('Width', validators=[DataRequired()])
    submit = SubmitField('Submit')

class AdjecentForm(FlaskForm):
    adjecent = BooleanField('')
    dep1 = StringField('Username')
    dep2 = StringField('Username')
