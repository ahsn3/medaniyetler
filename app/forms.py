from flask_wtf import FlaskForm
from wtforms import DecimalField, PasswordField, RadioField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField(validators=[DataRequired(), Length(min=2, max=80)])
    password = PasswordField(validators=[DataRequired()])
    submit = SubmitField()


class RegisterForm(FlaskForm):
    username = StringField(validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField(validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(validators=[DataRequired(), Length(min=8, max=128)])
    password2 = PasswordField(
        validators=[DataRequired(), EqualTo("password", message="match")]
    )
    submit = SubmitField()


class TransactionForm(FlaskForm):
    kind = RadioField(choices=[("income", "income"), ("expense", "expense")], validators=[DataRequired()])
    amount = DecimalField(
        validators=[DataRequired(), NumberRange(min=0.01, message="min")],
        places=2,
    )
    description = TextAreaField(validators=[Optional(), Length(max=2000)])
    submit = SubmitField()
