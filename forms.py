from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, NumberRange, Optional, Length

REQUEST_TYPES = [
    ("Corporate Retreat", "Corporate Retreat"),
    ("Corporate Incentive", "Corporate Incentive"),
    ("Meeting or Summit", "Meeting or Summit"),
    ("Brand Activation", "Brand Activation"),
]

BUDGET_RANGES = [
    ("Under $100k", "Under $100k"),
    ("$100k–250k", "$100k–250k"),
    ("$250k–500k", "$250k–500k"),
    ("$500k+", "$500k+"),
    ("Not sure yet", "Not sure yet"),
]


class EventBriefForm(FlaskForm):
    company = StringField("Company", validators=[DataRequired(), Length(max=200)])
    contact_name = StringField("Contact name", validators=[DataRequired(), Length(max=200)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=200)])
    phone = StringField("Phone", validators=[DataRequired(), Length(max=50)])
    country = StringField("Country", validators=[DataRequired(), Length(max=100)])
    request_type = SelectField("Type of request", choices=REQUEST_TYPES, validators=[DataRequired()])
    group_size = IntegerField("Group size", validators=[DataRequired(), NumberRange(min=1, max=5000)])
    preferred_dates = StringField("Preferred dates", validators=[DataRequired(), Length(max=100)])
    budget = SelectField("Average budget", choices=BUDGET_RANGES, validators=[DataRequired()])
    message = TextAreaField("Tell us about your event", validators=[Optional(), Length(max=4000)])
    # honeypot
    website = StringField("Website", validators=[Optional(), Length(max=0)])


class RfpForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=200)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=200)])
    company = StringField("Company", validators=[DataRequired(), Length(max=200)])
    rfp_file = FileField(
        "RFP document",
        validators=[FileRequired(), FileAllowed(["pdf", "doc", "docx", "ppt", "pptx"], "PDF, Word or PowerPoint files only.")],
    )
    website = StringField("Website", validators=[Optional(), Length(max=0)])


class CallbackForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=200)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=200)])
    company = StringField("Company", validators=[DataRequired(), Length(max=200)])
    phone = StringField("Phone", validators=[Optional(), Length(max=50)])
    website = StringField("Website", validators=[Optional(), Length(max=0)])


class AdminLoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=100)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=100)])
