# This file is a flask-wtf extension that uses a python class to represent a web form.
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
#from wtforms.validators import DataRequired

class SandtrailsForm(FlaskForm):
    track = SelectField('Track', 
                        choices=[('spiral', 'Spiral'),
                                 ('wiper', 'Wiper'),
                                 ('square', 'Square')])
    submit = SubmitField('Start')