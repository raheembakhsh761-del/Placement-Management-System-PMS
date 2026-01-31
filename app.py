"""
NAMAL PLACEMENT MANAGEMENT SYSTEM
Flask Application - Demonstrates All Four PBL Modules

DOMAIN MAPPING:
- Module A: Process students by CGPA priority (support programs)
- Module B: Instant lookup of students, opportunities, users
- Module C: Calculate city distances using Dijkstra's algorithm
- Module D: Display students in sorted order by CGPA
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
import logic
import secrets
import socket

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ==================== HOME & AUTH ====================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    MODULE B IN USE: Hash Table for O(1) user authentication
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # MODULE B: O(1) average case lookup
        user = logic.authenticate_user(username, password)
        
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            
            if user['role'] == 'Placement':
                return redirect(url_for('placement_dashboard'))
            elif user['role'] == 'Exam':
                return redirect(url_for('exam_dashboard'))
            elif user['role'] == 'Student':
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

# ==================== PLACEMENT DASHBOARD ====================

@app.route('/placement', methods=['GET', 'POST'])
def placement_dashboard():
    """
    DEMONSTRATES ALL MODULES:
    - Module A: Priority queue operations
    - Module B: Hash table for duplicate checking and lookups
    - Module C: Dijkstra for distance calculation
    - Module D: BST for sorted student display
    """
    if session.get('role') != 'Placement':
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'action' in request.form and request.form['action'] == 'register_student':
            reg_no = request.form.get('reg_no', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            program = request.form.get('program', '').strip()
            password = request.form.get('password', '').strip()
            
            if all([reg_no, name, email, program, password]):
                # MODULES A, B, D: All structures updated on registration
                success, message = logic.register_new_student(reg_no, name, email, program, password)
                flash(f"{'✅' if success else '❌'} {message}", 'success' if success else 'error')
            else:
                flash('❌ All fields are required', 'error')
        
        elif 'action' in request.form and request.form['action'] == 'post_opportunity':
            opp_id = request.form.get('opp_id', '').strip()
            title = request.form.get('title', '').strip()
            opp_type = request.form.get('type', '').strip()
            min_cgpa = request.form.get('min_cgpa', '').strip()
            link = request.form.get('link', '').strip()
            details = request.form.get('details', '').strip()
            location = request.form.get('location', '').strip()
            
            if all([opp_id, title, opp_type, min_cgpa, link, location]):
                # MODULES B & C: Hash table + Dijkstra's algorithm
                success, message = logic.post_new_opportunity(
                    opp_id, title, opp_type, min_cgpa, link, details, location
                )
                flash(f"{'✅' if success else '❌'} {message}", 'success' if success else 'error')
            else:
                flash('❌ All required fields must be filled', 'error')
    
    # MODULE D: Get students sorted by CGPA using BST
    students = logic.get_students_sorted_by_cgpa()
    
    # MODULE B: Get opportunities from hash table
    opportunities = logic.read_csv('opportunities.csv')
    stats = logic.get_system_statistics()
    
    # Calculate eligible students for each opportunity
    for opp in opportunities:
        eligible = logic.get_eligible_students(opp.get('min_cgpa', 0))
        opp['eligible_count'] = len(eligible)
        opp['eligible_names'] = ', '.join([s['name'] for s in eligible[:5]])
        if len(eligible) > 5:
            opp['eligible_names'] += f' and {len(eligible) - 5} more...'
    
    return render_template('placement_dashboard.html', 
                         students=students, 
                         opportunities=opportunities, 
                         stats=stats)

# ==================== EXAM DASHBOARD ====================

@app.route('/exam', methods=['GET', 'POST'])
def exam_dashboard():
    """
    DEMONSTRATES MODULES A, B, D:
    - Update student GPA (affects heap, hash, BST)
    - Display sorted students (BST)
    """
    if session.get('role') != 'Exam':
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        reg_no = request.form.get('reg_no', '').strip()
        gpa = request.form.get('gpa', '').strip()
        
        if reg_no and gpa:
            try:
                gpa_float = float(gpa)
                if 0.0 <= gpa_float <= 4.0:
                    # MODULES A, B, D: All structures updated
                    success, message = logic.update_student_gpa(reg_no, gpa)
                    flash(f"{'✅' if success else '❌'} {message}", 'success' if success else 'error')
                else:
                    flash('❌ GPA must be between 0.0 and 4.0', 'error')
            except ValueError:
                flash('❌ Invalid GPA value', 'error')
        else:
            flash('❌ All fields are required', 'error')
    
    # MODULE D: Get sorted students from BST (returns list format for HTML)
    students = logic.get_students_sorted_by_cgpa()
    stats = logic.get_system_statistics()
    
    return render_template('exam_dashboard.html', students=students, stats=stats)

# ==================== STUDENT DASHBOARD ====================

@app.route('/student')
def student_dashboard():
    """
    DEMONSTRATES MODULES B & C:
    - Hash table for student lookup
    - Dijkstra for sorting opportunities by distance
    """
    if session.get('role') != 'Student':
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    
    reg_no = session.get('username')
    
    # MODULE B: O(1) student lookup using hash table
    student = logic.get_student_by_regno(reg_no)
    
    if not student:
        flash('❌ Student record not found', 'error')
        return render_template('student_dashboard.html', 
                             student=None, 
                             opportunities=[], 
                             gpa_history=[])
    
    # Parse GPA history
    gpa_history = student.get('gpa_history', '').split('|') if student.get('gpa_history') else []
    
    # Get eligible opportunities
    all_opportunities = logic.read_csv('opportunities.csv')
    eligible_opportunities = []
    student_cgpa = float(student.get('cgpa', 0))
    
    for opp in all_opportunities:
        try:
            if student_cgpa >= float(opp.get('min_cgpa', 0)):
                dist = opp.get('distance', 'Unknown')
                # MODULE C: Distance calculated via Dijkstra's algorithm
                opp['distance_km'] = int(dist) if str(dist).isdigit() else 999999
                eligible_opportunities.append(opp)
        except:
            continue
    
    # Sort by distance (closest first)
    eligible_opportunities.sort(key=lambda x: x['distance_km'])
    
    return render_template('student_dashboard.html', 
                         student=student, 
                         opportunities=eligible_opportunities, 
                         gpa_history=gpa_history)

# ==================== HELPERS & RUN ====================

def get_local_ip():
    """Find local IP address for network access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    ip = get_local_ip()
    port = 5000
    

    # Host on network, allow multiple simultaneous connections
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)