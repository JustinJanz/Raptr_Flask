from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


    def validate_username(self,username):
        from raptr import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('User name already exists!')

    def validate_email(self,email):
        from raptr import User
        user = User.query.filter_by(email = email.data).first()
        if user:
            raise ValidationError('email already exists!')


class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class summary_url(FlaskForm):
    url = StringField('url',validators=[DataRequired()])
    submit = SubmitField('Summarize')

class get_summary(FlaskForm):
    submit = SubmitField('get_summary')