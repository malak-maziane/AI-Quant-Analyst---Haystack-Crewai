from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField
from wtforms.validators import DataRequired, Length

class AnalysisForm(FlaskForm):
    """
    WTForms form for the stock analysis input.
    Includes ticker field and optional PDF upload.
    """
    ticker = StringField(
        'Stock Ticker',
        validators=[
            DataRequired(),
            Length(min=1, max=10, message="Ticker must be 1-10 characters")
        ],
        render_kw={"placeholder": "e.g. AAPL"}
    )
    
    document = FileField(
        'Financial Document (optional)',
        validators=[],
        render_kw={"accept": ".pdf,.txt"}
    )

    question = StringField(
        'Question (Optional)',
        validators=[Length(max=200, message="Question cannot exceed 200 characters")],
        render_kw={"placeholder": "e.g. What are the main risks for AAPL?"}
    )
    
    submit = SubmitField('Analyze Stock')