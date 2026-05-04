import os
import json
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app.forms import AnalysisForm
from app.crew import QuantAnalystCrew
from app.utils import validate_ticker, sanitize_upload, get_company_name

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Landing page with analysis form."""
    form = AnalysisForm()
    return render_template('index.html', form=form)

@bp.route('/analyze', methods=['POST'])
def analyze():
    """Handle form submission and start analysis."""
    form = AnalysisForm()
    
    if form.validate_on_submit():
        ticker = form.ticker.data.upper()
        
        # Validate ticker
        if not validate_ticker(ticker):
            flash('Invalid stock ticker. Please try again.', 'error')
            return redirect(url_for('main.index'))
        
        # Handle file upload
        document_path = None
        if form.document.data:
            filename = sanitize_upload(form.document.data.filename)
            if filename:
                upload_path = os.path.join(os.path.dirname(__file__), '..', 'uploads', filename)
                form.document.data.save(upload_path)
                document_path = upload_path

        # Optional QA question
        question = form.question.data.strip() if form.question.data else None
        
        # Run analysis
        try:
            crew = QuantAnalystCrew(ticker, document_path, question)
            result = crew.run()
            session['analysis_result'] = result
            return redirect(url_for('main.result'))
        except Exception as e:
            flash(f'Analysis failed: {str(e)}', 'error')
            return redirect(url_for('main.index'))
    
    # Form validation failed
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'error')
    return redirect(url_for('main.index'))

@bp.route('/result')
def result():
    """Display analysis results."""
    result = session.get('analysis_result')
    if not result:
        flash('No analysis results found. Please start a new analysis.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('result.html', result=result)

@bp.route('/api/analyze', methods=['GET', 'POST'])
def api_analyze():
    """JSON API endpoint for analysis."""
    if request.method == 'GET':
        ticker = request.args.get('ticker')
    else:
        data = request.get_json()
        ticker = data.get('ticker') if data else None
    
    if not ticker:
        return jsonify({"error": "Ticker parameter required"}), 400
    
    ticker = ticker.upper()
    if not validate_ticker(ticker):
        return jsonify({"error": "Invalid ticker"}), 400
    
    try:
        crew = QuantAnalystCrew(ticker)
        result = crew.run()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "version": "1.0.0"
    })

@bp.route('/api/status')
def api_status():
    """Status endpoint for loading page polling."""
    # In a real implementation, this would check the status of the analysis
    return jsonify({"status": "running", "progress": 75})