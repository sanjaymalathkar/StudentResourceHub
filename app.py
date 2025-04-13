from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify , send_file
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import Flask, request, redirect, url_for, flash, render_template
from flask_pymongo import PyMongo
import gridfs
import io
from datetime import datetime
from gridfs import GridFS
from werkzeug.utils import secure_filename  # ✅ Import this!
from bson import ObjectId
import re



app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ✅ Correct: Set MongoDB URI before initializing PyMongo
app.config["MONGO_URI"] = "mongodb://localhost:27017/MES_RESOURCE"
mongo = PyMongo(app)

# ✅ Use mongo.db instead of client
db = mongo.db  
teachers = db["teachers"]
students = db["students"]
admin = db["admins"]
chat_db = db  # Using the same MongoDB for chat
messages = chat_db["messages"]
attendance_collection = db["attendance"]
students_collection = db["student"]

# ✅ Initialize GridFS properly
fs = gridfs.GridFS(db)



# Set up static and template folders
app.static_folder = 'static'
app.template_folder = 'template'

# Home Page
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/programs')
def programs():
    return render_template('programs.html')

@app.route('/admisiions')
def admissions():
    return render_template('admissions.html')

# About Page
@app.route("/about")
def about():
    return render_template("about.html")

# Contact Page
@app.route("/contact")
def contact():
    return render_template("contact.html")

# Directory for file uploads
uploads_dir = os.path.join(os.getcwd(), "uploads")
os.makedirs(uploads_dir, exist_ok=True)

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    teacher_count = teachers.count_documents({})
    student_count = students.count_documents({})
    
    return render_template('admin_dashboard.html', teacher_count=teacher_count, student_count=student_count)

@app.route('/get_counts')
def get_counts():
    teacher_count = teachers.count_documents({})
    student_count = students.count_documents({})
    
    return {"teachers": teacher_count, "students": student_count}  # Returns JSON response
@app.route('/logout')
def logout():
    session.pop('teacher_id', None)  # Clearing session data
    return redirect(url_for('teacherlogin'))  # Redirecting to login page


@app.route('/resources', methods=['GET', 'POST'])
def resources():
    # Logic for handling resources
    return render_template('resources.html')

# Route to display attendance form and submit attendance
@app.route('/take_attendance', methods=['GET', 'POST'])
def take_attendance():
    if request.method == 'POST':
        date = request.form['date']
        student_ids = request.form.getlist('attendance')  # Selected student IDs

        if not student_ids:
            flash("⚠️ Please select at least one student!", "danger")
            return redirect(url_for('take_attendance'))

        for student_id in student_ids:
            attendance_data = {
                "date": date,
                "student_id": student_id,
                "status": "Present",
                "timestamp": datetime.now()
            }
            attendance_collection.insert_one(attendance_data)

        flash("✅ Attendance marked successfully!", "success")
        return redirect(url_for('take_attendance'))

    # Fetch students
    student_list = list(students_collection.find({}, {"_id": 0, "fullname": 1, "roll_number": 1}))

    # Get last 5 days attendance
    last_5_days = datetime.now() - timedelta(days=5)
    attendance_records = list(attendance_collection.find(
        {"timestamp": {"$gte": last_5_days}},  # Get attendance from last 5 days
        {"_id": 0, "date": 1, "student_id": 1, "status": 1}  # Fetch required fields
    ))

    # Convert attendance records into a dictionary for easy lookup
    attendance_history = {}
    for record in attendance_records:
        if record["student_id"] not in attendance_history:
            attendance_history[record["student_id"]] = []
        attendance_history[record["student_id"]].append((record["date"], record["status"]))

    return render_template('take_attendance.html', students=student_list, attendance_history=attendance_history)

@app.route('/add_activity', methods=['GET', 'POST'])
def add_activity():
    return render_template('add_activity.html')  # Ensure this file exists in 'templates' folder

@app.route('/upload_youtube', methods=['GET', 'POST'])
def upload_youtube():
    return render_template('upload_youtube.html')  # Ensure this file exists in 'templates' folder

@app.route('/create_student', methods=['POST'])
def create_student():
    if request.method == 'POST':
        student_fullname = request.form.get('student_fullname')
        student_roll = request.form.get('student_roll')

        if not student_fullname or not student_roll:
            flash("All fields are required!", "danger")
            return redirect(url_for('index'))

        student_data = {
            "fullname": student_fullname,
            "roll_number": student_roll,
            "created_at": datetime.datetime.utcnow()  # Store the timestamp
        }

        result = students_collection.insert_one(student_data)

        if result.inserted_id:
            flash("Student added successfully!", "success")
        else:
            flash("Failed to add student.", "danger")

        return redirect(url_for('teacher_dashboard'))  # Redirect back to homepage


# Add Teacher
@app.route('/admin/add_teacher', methods=['POST'])
def add_teacher():
    if 'admin_id' not in session:
        flash('Unauthorized Access!', 'danger')
        return redirect(url_for('admin_login'))
    
    name = request.form['teacher_name']
    email = request.form['teacher_email']
    password = generate_password_hash(request.form['teacher_password'])
    teachers.insert_one({'name': name, 'email': email, 'password': password})
    flash('Teacher added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Add Student
@app.route('/admin/add_student', methods=['POST'])
def add_student():
    if 'admin_id' not in session:
        flash('Unauthorized Access!', 'danger')
        return redirect(url_for('admin_login'))
    
    name = request.form['student_name']
    email = request.form['student_email']
    password = generate_password_hash(request.form['student_password'])
    students.insert_one({'name': name, 'email': email, 'password': password})
    flash('Student added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Admin Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

# Teacher Login System
@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = teachers.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            session['teacher_id'] = str(user['_id'])
            flash('Login successful!', 'success')
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('teacherlogin.html')

@app.route('/teacher/forgot-password', methods=['GET', 'POST'])
def teacher_forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = teachers.find_one({'email': email})

        if user:
            flash('Password reset link sent to your email!', 'info')
        else:
            flash('Email not found!', 'danger')

    return render_template('forgot_password.html')

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('teacher_login'))
    
    # Fetch resources with type != notes or no type specified
    resources_cursor = fs.find({"metadata.type": {"$ne": "notes"}})
    
    # Convert GridOut objects to dictionaries
    resources = []
    for resource in resources_cursor:
        # Create a dictionary with necessary fields from the GridOut object
        resource_dict = {
            "_id": str(resource._id),
            "filename": resource.filename,
            "content_type": resource.content_type,
            "upload_date": resource.upload_date if hasattr(resource, 'upload_date') else None
        }
        # Add metadata if available
        if hasattr(resource, 'metadata') and resource.metadata:
            for key, value in resource.metadata.items():
                resource_dict[key] = value
        resources.append(resource_dict)
    
    # Fetch notes specifically
    notes_cursor = fs.find({"metadata.type": "notes"})
    
    # Convert GridOut objects to dictionaries
    notes = []
    for note in notes_cursor:
        # Create a dictionary with necessary fields from the GridOut object
        note_dict = {
            "_id": str(note._id),
            "filename": note.filename,
            "content_type": note.content_type,
            "upload_date": note.upload_date if hasattr(note, 'upload_date') else None
        }
        # Add metadata if available
        if hasattr(note, 'metadata') and note.metadata:
            for key, value in note.metadata.items():
                note_dict[key] = value
        notes.append(note_dict)
    
    return render_template('teacher_dashboard.html', resources=resources, notes=notes)

@app.route('/teacher/logout')
def logout_teacher():
    session.pop('teacher_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('teacher_login'))

# Teacher File Upload System



    # 🔹 Retrieve File List
@app.route('/view_resources')
def view_resources():
    files_cursor = fs.find()
    
    # Convert GridOut objects to dictionaries
    files = []
    for file_doc in files_cursor:
        file_dict = {
            "_id": str(file_doc._id),
            "filename": file_doc.filename,
            "content_type": file_doc.content_type,
            "upload_date": file_doc.upload_date if hasattr(file_doc, 'upload_date') else None
        }
        files.append(file_dict)
        
    return render_template('view_resouces.html', files=files)

# 🔹 Download File Route
@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(file_id):
            flash("⚠️ Invalid file ID format!", "danger")
            return redirect(url_for('teacher_dashboard'))
        
        # Get file from GridFS
        file = fs.get(ObjectId(file_id))
        
        # Create file buffer
        file_buffer = io.BytesIO(file.read())
        
        # Get content type and filename
        content_type = file.content_type if hasattr(file, 'content_type') else 'application/octet-stream'
        filename = file.filename if hasattr(file, 'filename') else 'download.bin'
        
        # Return file
        return send_file(
            file_buffer,
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        flash(f"⚠️ Error downloading file: {str(e)}", "danger")
        return redirect(url_for('teacher_dashboard'))

@app.route('/upload_resources', methods=['POST'])
def upload_resources():
    try:
        # Check if teacher is logged in
        if 'teacher_id' not in session:
            flash("Please login first!", "warning")
            return redirect(url_for('teacher_login'))
            
        course = request.form.get('course', '').strip().upper()
        year = request.form.get('year', '').strip()
        module = request.form.get('module', '').strip()
        subject = request.form.get('subject', '').strip()
        file = request.files.get('file')

        print(f"DEBUG: Processing file upload - Course: {course}, Year: {year}, Module: {module}")
        
        # ✅ Validate Course Name (Allow only letters, numbers, and spaces)
        if not re.match(r"^[A-Za-z0-9 ]+$", course):
            error_msg = "⚠️ Invalid course name format!"
            flash(error_msg, "danger")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(error=error_msg)
            return redirect(url_for('teacher_dashboard'))

        # ✅ Validate File
        if not file or file.filename == "":
            error_msg = "⚠️ No file uploaded!"
            flash(error_msg, "danger")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(error=error_msg)
            return redirect(url_for('teacher_dashboard'))

        filename = secure_filename(file.filename)
        print(f"DEBUG: Saving file: {filename}")

        # Get upload timestamp
        upload_timestamp = datetime.now()
        
        # Prepare structured metadata that matches our query formats
        file_metadata = {
            "type": "resource",
            "course": course,
            "year": year,
            "module": module,
            "subject": subject,
            "upload_date": upload_timestamp
        }
        
        print(f"DEBUG: Prepared metadata: {file_metadata}")
        
        # Store File in GridFS with metadata
        file_id = fs.put(file, 
                         filename=filename, 
                         content_type=file.content_type,
                         metadata=file_metadata)
        
        print(f"DEBUG: File saved in GridFS with ID: {file_id}")

        # Also store metadata in MongoDB resources collection for backward compatibility
        mongo.db.resources.insert_one({
            "course": course,
            "year": year,
            "module": module,
            "subject": subject,
            "file_id": str(file_id),
            "filename": filename,
            "upload_date": upload_timestamp
        })

        success_msg = "✅ File uploaded successfully!"
        flash(success_msg, "success")
        
        # Return JSON if it's an AJAX request, otherwise redirect
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(message=success_msg)
        return redirect(url_for('teacher_dashboard'))

    except Exception as e:
        error_msg = f"❌ An error occurred: {str(e)}"
        print(f"DEBUG ERROR: {error_msg}")
        flash(error_msg, "danger")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(error=error_msg)
        return redirect(url_for('teacher_dashboard'))

@app.route("/upload_notes", methods=["GET", "POST"])
def upload_notes():
    if request.method == "GET":
        return render_template("upload_notes.html")  # Show the upload page

    if "teacher_id" not in session:
        flash("❌ Unauthorized access!", "danger")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(error="❌ Unauthorized access!")
        return redirect(url_for('teacher_login'))

    try:
        course = request.form.get("course", "").strip().upper()
        year = request.form.get("year")
        module = request.form.get("module")
        subject = request.form.get("subject")
        file = request.files.get("file")

        print(f"DEBUG: Processing notes upload - Course: {course}, Year: {year}, Module: {module}")

        if not course:
            error_msg = "⚠️ Course is required!"
            flash(error_msg, "danger")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(error=error_msg)
            return redirect(url_for('teacher_dashboard'))

        if not file:
            error_msg = "⚠️ No file uploaded!"
            flash(error_msg, "danger")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(error=error_msg)
            return redirect(url_for('teacher_dashboard'))

        filename = secure_filename(file.filename)
        print(f"DEBUG: Saving notes file: {filename}")
        
        # Get upload timestamp
        upload_timestamp = datetime.now()
        
        # Prepare structured metadata that matches our query formats
        file_metadata = {
            "type": "notes",
            "course": course,
            "year": year,
            "module": module,
            "subject": subject,
            "upload_date": upload_timestamp
        }
        
        print(f"DEBUG: Prepared notes metadata: {file_metadata}")
        
        # Store File in GridFS with metadata
        file_id = fs.put(file, 
                         filename=filename, 
                         content_type=file.content_type,
                         metadata=file_metadata)
        
        print(f"DEBUG: Notes file saved in GridFS with ID: {file_id}")

        # Also store metadata in MongoDB resources collection for backward compatibility
        mongo.db.notes.insert_one({
            "course": course,
            "year": year,
            "module": module,
            "subject": subject,
            "file_id": str(file_id),
            "filename": filename,
            "upload_date": upload_timestamp
        })

        success_msg = "✅ File uploaded successfully!"
        flash(success_msg, "success")
        
        # Return JSON if it's an AJAX request, otherwise redirect
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(message=success_msg)
        return redirect(url_for('teacher_dashboard'))

    except Exception as e:
        error_msg = f"❌ An error occurred: {str(e)}"
        print(f"DEBUG ERROR: {error_msg}")
        flash(error_msg, "danger")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(error=error_msg)
        return redirect(url_for('teacher_dashboard'))


@app.route('/teacher/upload_questions', methods=['POST'])
def upload_questions():
    if 'teacher_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('teacher_login'))

    file = request.files['question_file']
    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join(uploads_dir, file.filename)
        file.save(file_path)
        flash('Question paper uploaded successfully!', 'success')
    else:
        flash('Invalid file type. Only PDFs allowed.', 'danger')

    return redirect(url_for('teacher_dashboard'))

# Student Login
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # ✅ Fetch student from MongoDB correctly
        user = mongo.db.students.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            session['student_id'] = str(user['_id'])  # ✅ Store student ID in session
            flash('Login successful!', 'success')

            # ✅ Redirect to the correct function
            return redirect(url_for('student_dashboard'))  # 🔥 FIXED!
        else:
            flash('Invalid email or password', 'danger')

    return render_template('studentlogin.html')




@app.route('/student/forgot-password', methods=['GET', 'POST'])
def student_forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = students.find_one({'email': email})

        if user:
            flash('Password reset link sent to your email!', 'info')
        else:
            flash('Email not found!', 'danger')

    return render_template('forgot_password.html')

# 🚀 Student Dashboard Route
@app.route('/student/dashboard', methods=['GET', 'POST'])
def student_dashboard():
    # Check if user is logged in (if login is required)
    if 'student_id' not in session and app.config.get('REQUIRE_LOGIN', False):
        flash("⚠️ Please login first!", "error")
        return redirect(url_for('student_login'))

    # Initialize variables that will be passed to the template
    resources = []
    question_papers = []
    youtube_links = []
    available_modules = []
    selected_course = None
    selected_year = None
    selected_module = "all"

    if request.method == 'POST':
        try:
            # Get form data
            course = request.form.get('course')
            year = request.form.get('year')
            module = request.form.get('module', 'all')  # Default to 'all' if no module provided
            
            # Debug the incoming form data
            print(f"DEBUG: Student dashboard form data: course={course}, year={year}, module={module}")
            
            # Validate required fields
            if not course or not year:
                flash("Please select Course and Year", "error")
                return redirect(url_for('student_dashboard'))
            
            # Set the selected values for the template
            selected_course = course.upper()
            selected_year = year
            selected_module = module

            # Create MongoDB query based on filter parameters
            if module and module.lower() != "all":
                mongodb_query = {
                    "course": selected_course,
                    "year": selected_year,
                    "module": module.strip()
                }
            else:
                # If no specific module or "all" is selected, get all for this course and year
                mongodb_query = {
                    "course": selected_course,
                    "year": selected_year
                }
            
            print(f"DEBUG: Using MongoDB query: {mongodb_query}")
            
            try:
                # Fetch resources from resources collection
                mongodb_resources = list(mongo.db.resources.find(mongodb_query).sort("upload_date", -1))
                print(f"DEBUG: Found {len(mongodb_resources)} resources in MongoDB collection")
                
                # Convert MongoDB resources to dictionary format
                for resource in mongodb_resources:
                    resource_dict = {
                        "_id": str(resource["_id"]),
                        "filename": resource.get("filename", "Unknown"),
                        "course": resource.get("course", ""),
                        "year": resource.get("year", ""),
                        "module": resource.get("module", ""),
                        "subject": resource.get("subject", ""),
                        "upload_date": resource.get("upload_date", None)
                    }
                    
                    # Add file_id if it exists
                    if "file_id" in resource:
                        resource_dict["file_id"] = str(resource["file_id"])
                    
                    resources.append(resource_dict)
                
                # Get question papers
                try:
                    mongodb_question_papers = list(mongo.db.question_papers.find(mongodb_query).sort("upload_date", -1))
                    for paper in mongodb_question_papers:
                        paper_dict = {
                            "_id": str(paper["_id"]),
                            "filename": paper.get("filename", "Unknown"),
                            "course": paper.get("course", ""),
                            "year": paper.get("year", ""),
                            "module": paper.get("module", ""),
                            "subject": paper.get("subject", ""),
                            "upload_date": paper.get("upload_date", None)
                        }
                        
                        if "file_id" in paper:
                            paper_dict["file_id"] = str(paper["file_id"])
                        
                        question_papers.append(paper_dict)
                except Exception as e:
                    print(f"Error fetching question papers: {str(e)}")
                
                # Get YouTube links
                try:
                    mongodb_youtube_links = list(mongo.db.youtube_links.find(mongodb_query).sort("upload_date", -1))
                    for link in mongodb_youtube_links:
                        link_dict = {
                            "_id": str(link["_id"]),
                            "title": link.get("title", "YouTube Video"),
                            "url": link.get("url", ""),
                            "course": link.get("course", ""),
                            "year": link.get("year", ""),
                            "module": link.get("module", ""),
                            "subject": link.get("subject", ""),
                            "upload_date": link.get("upload_date", None)
                        }
                        
                        youtube_links.append(link_dict)
                except Exception as e:
                    print(f"Error fetching YouTube links: {str(e)}")
                
                # Get list of all modules for this course and year for the filter dropdown
                modules_set = set()
                try:
                    # Add modules from MongoDB collections
                    modules_cursor = mongo.db.resources.find(
                        {"course": selected_course, "year": selected_year}, 
                        {"module": 1}
                    )
                    for doc in modules_cursor:
                        if "module" in doc and doc["module"]:
                            modules_set.add(doc["module"])
                            
                    # Add modules from question papers
                    modules_cursor = mongo.db.question_papers.find(
                        {"course": selected_course, "year": selected_year}, 
                        {"module": 1}
                    )
                    for doc in modules_cursor:
                        if "module" in doc and doc["module"]:
                            modules_set.add(doc["module"])
                            
                    # Add modules from YouTube links
                    modules_cursor = mongo.db.youtube_links.find(
                        {"course": selected_course, "year": selected_year}, 
                        {"module": 1}
                    )
                    for doc in modules_cursor:
                        if "module" in doc and doc["module"]:
                            modules_set.add(doc["module"])
                except Exception as e:
                    print(f"Error fetching modules: {str(e)}")
                
                # Sort the modules alphabetically
                available_modules = sorted(list(modules_set))
                
                print(f"DEBUG: Final counts - {len(resources)} resources, {len(question_papers)} question papers, {len(youtube_links)} YouTube links")
                print(f"DEBUG: Available modules: {available_modules}")
                
            except Exception as e:
                print(f"Error fetching data from MongoDB collections: {str(e)}")
                import traceback
                print(f"DEBUG: Exception traceback: {traceback.format_exc()}")
                flash(f"Error retrieving resources: {str(e)}", "error")
                
        except Exception as e:
            flash(f"Error processing request: {str(e)}", "error")
            print(f"ERROR in student_dashboard POST: {str(e)}")
            import traceback
            print(f"DEBUG: Exception traceback: {traceback.format_exc()}")

    # Render the template with all data
    return render_template('student_dashboard.html',
                          resources=resources,
                          question_papers=question_papers,
                          youtube_links=youtube_links,
                          available_modules=available_modules,
                          selected_course=selected_course,
                          selected_year=selected_year,
                          selected_module=selected_module,
                          debug=app.debug)


@app.route('/download/<resource_id>')
def download_resource(resource_id):
    try:
        # ✅ Validate ObjectId
        if not ObjectId.is_valid(resource_id):  # Ensure it's a valid 24-character hex ObjectId
            flash("⚠️ Invalid file ID!", "danger")
            return redirect(url_for('student_dashboard'))

        # First try to get the file directly from GridFS
        try:
            file_data = fs.get(ObjectId(resource_id))
            print(f"DEBUG: Found file directly in GridFS with ID: {resource_id}")
        except Exception as e:
            print(f"DEBUG: Could not find file in GridFS directly: {str(e)}")
            
            # If not found directly, look up in collections for file_id reference
            # Try resources collection first
            resource = mongo.db.resources.find_one({"_id": ObjectId(resource_id)})
            if resource and "file_id" in resource:
                try:
                    # Try to get the actual file from GridFS using the file_id reference
                    file_data = fs.get(ObjectId(resource["file_id"]))
                    print(f"DEBUG: Found file in GridFS via resources collection, file_id: {resource['file_id']}")
                except Exception as e:
                    print(f"DEBUG: Error retrieving file referenced in resources: {str(e)}")
                    flash("⚠️ Referenced file not found in GridFS!", "danger")
                    return redirect(url_for('student_dashboard'))
            else:
                # Try notes collection next
                note = mongo.db.notes.find_one({"_id": ObjectId(resource_id)})
                if note and "file_id" in note:
                    try:
                        # Try to get the actual file from GridFS using the file_id reference
                        file_data = fs.get(ObjectId(note["file_id"]))
                        print(f"DEBUG: Found file in GridFS via notes collection, file_id: {note['file_id']}")
                    except Exception as e:
                        print(f"DEBUG: Error retrieving file referenced in notes: {str(e)}")
                        flash("⚠️ Referenced file not found in GridFS!", "danger")
                        return redirect(url_for('student_dashboard'))
                else:
                    flash("⚠️ Resource not found in any collection!", "danger")
                    return redirect(url_for('student_dashboard'))

        # ✅ Ensure File Exists
        if not file_data:
            flash("⚠️ No file found with this ID!", "danger")
            return redirect(url_for('student_dashboard'))

        # ✅ Get filename and content type
        filename = file_data.filename if hasattr(file_data, 'filename') else "downloaded_file"
        mimetype = file_data.content_type if hasattr(file_data, 'content_type') else "application/octet-stream"

        return send_file(
            io.BytesIO(file_data.read()),  # Read file into memory
            mimetype=mimetype,  
            as_attachment=True,  
            download_name=filename  
        )

    except Exception as e:
        print(f"ERROR in download_resource: {str(e)}")
        flash(f"⚠️ Error downloading file: {str(e)}", "danger")
        return redirect(url_for('student_dashboard'))  # Redirect if download fails

# 🔹 Route for Teacher Upload Page
@app.route('/upload_resources_page')
def upload_resources_page():
    return render_template('teacher_upload.html')  # Ensure this template exists


@app.route("/teacher_logout")
def teacher_logout():
    session.pop("teacher_id", None)  # Instead of session.clear()
    return redirect("/teacher_login")


@app.route('/student/logout')
def logout_student():
    session.pop('student_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('student_login'))

# Admin Login System
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = admin.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            session['admin_id'] = str(user['_id'])
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('adminlogin.html')

# Chat System
@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.json
    username = data.get("username")
    message = data.get("message")
    course = data.get("course")

    if not username or not message:
        return jsonify({"error": "Missing data"}), 400

    messages.insert_one({
        "username": username,
        "message": message,
        "course": course,
        "timestamp": datetime.datetime.utcnow()
    })
    return jsonify({"success": True})

# API route to get available modules for a course and year
@app.route('/api/get_modules', methods=['GET'])
def get_modules():
    course = request.args.get('course', '').upper()
    year = request.args.get('year', '')
    
    if not course or not year:
        return jsonify({"error": "Course and year are required parameters", "modules": []}), 400
    
    print(f"DEBUG: Fetching modules for course={course}, year={year}")
    
    available_modules = set()
    try:
        # Get modules from GridFS metadata
        modules_cursor = fs.find({"metadata.course": course, "metadata.year": year})
        for doc in modules_cursor:
            if hasattr(doc, 'metadata') and doc.metadata and "module" in doc.metadata and doc.metadata["module"]:
                available_modules.add(doc.metadata["module"])
                
        # Add modules from MongoDB collections
        # Resources collection
        modules_cursor = mongo.db.resources.find({"course": course, "year": year}, {"module": 1})
        for doc in modules_cursor:
            if "module" in doc and doc["module"]:
                available_modules.add(doc["module"])
        
        # Notes collection
        modules_cursor = mongo.db.notes.find({"course": course, "year": year}, {"module": 1})
        for doc in modules_cursor:
            if "module" in doc and doc["module"]:
                available_modules.add(doc["module"])
                
        # Question papers collection
        try:
            modules_cursor = mongo.db.question_papers.find({"course": course, "year": year}, {"module": 1})
            for doc in modules_cursor:
                if "module" in doc and doc["module"]:
                    available_modules.add(doc["module"])
        except Exception:
            # Collection might not exist, just ignore
            pass
                
        # Sort the modules alphabetically
        sorted_modules = sorted(list(available_modules))
        
        print(f"DEBUG: Found modules for {course} {year}: {sorted_modules}")
        
        return jsonify({"modules": sorted_modules})
        
    except Exception as e:
        print(f"Error fetching modules: {str(e)}")
        import traceback
        print(f"DEBUG: Exception traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e), "modules": []}), 500

# Test route for debugging dashboard display
@app.route('/test/create_resource')
def test_create_resource():
    """Create a test resource and redirect to dashboard"""
    try:
        # Create a test file
        test_content = b"This is a test file created for debugging the dashboard display."
        
        # Set parameters that match student input form
        course = "BCA"
        year = "1st Year"
        module = "Programming"
        
        # Prepare metadata
        metadata = {
            "type": "resource",
            "course": course,
            "year": year,
            "module": module,
            "subject": "Test Subject",
            "upload_date": datetime.now()
        }
        
        # Store in GridFS
        file_id = fs.put(
            test_content,
            filename="test_resource.txt",
            content_type="text/plain",
            metadata=metadata
        )
        
        # Also store in MongoDB for backward compatibility
        mongo.db.resources.insert_one({
            "course": course,
            "year": year,
            "module": module,
            "subject": "Test Subject",
            "file_id": str(file_id),
            "filename": "test_resource.txt",
            "upload_date": datetime.now()
        })
        
        flash("Test resource created successfully!", "success")
        
        # Format the URL parameters to match the course_dashboard route
        formatted_year = year.replace(" ", "-").lower()
        return redirect(url_for('course_dashboard', 
                              course=course.lower(), 
                              year=formatted_year, 
                              module=module))
        
    except Exception as e:
        print(f"Error creating test resource: {str(e)}")
        flash(f"Error creating test resource: {str(e)}", "danger")
        return redirect(url_for('student_dashboard'))

# Enhanced debug route for checking database contents
@app.route('/debug/resources')
def debug_resources():
    if not app.debug:
        return "Debug mode disabled. Enable debug mode to use this route.", 403
        
    # Get resources from various collections
    resources = list(mongo.db.resources.find().sort("_id", -1))
    notes = list(mongo.db.notes.find().sort("_id", -1))
    
    # Convert ObjectIds to strings for display
    for resource in resources:
        resource["_id"] = str(resource["_id"])
        if "file_id" in resource:
            resource["file_id"] = str(resource["file_id"])
    
    for note in notes:
        note["_id"] = str(note["_id"])
        if "file_id" in note:
            note["file_id"] = str(note["file_id"])
    
    # Get files from GridFS with more detailed information
    gridfs_files = []
    metadata_counts = {
        "has_type": 0,
        "has_course": 0,
        "has_year": 0,
        "has_module": 0,
        "has_subject": 0,
        "type_resource": 0,
        "type_notes": 0
    }
    
    for file_doc in fs.find():
        file_dict = {
            "_id": str(file_doc._id),
            "filename": file_doc.filename,
            "uploadDate": file_doc.upload_date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(file_doc, 'upload_date') else "N/A",
        }
        
        # Add metadata if available and track statistics
        if hasattr(file_doc, 'metadata') and file_doc.metadata:
            file_dict["metadata"] = {}
            for key, value in file_doc.metadata.items():
                file_dict["metadata"][key] = value
                
                # Track metadata statistics
                if key == 'type':
                    metadata_counts["has_type"] += 1
                    if value == 'resource':
                        metadata_counts["type_resource"] += 1
                    elif value == 'notes':
                        metadata_counts["type_notes"] += 1
                elif key == 'course':
                    metadata_counts["has_course"] += 1
                elif key == 'year':
                    metadata_counts["has_year"] += 1
                elif key == 'module':
                    metadata_counts["has_module"] += 1
                elif key == 'subject':
                    metadata_counts["has_subject"] += 1
        else:
            file_dict["metadata"] = {}
            
        gridfs_files.append(file_dict)
    
    # Build statistics summary
    available_courses = set()
    available_years = set()
    available_modules = set()
    
    # Get distinct courses, years, and modules from GridFS metadata
    for file_doc in gridfs_files:
        if "metadata" in file_doc and file_doc["metadata"]:
            if "course" in file_doc["metadata"]:
                available_courses.add(file_doc["metadata"]["course"])
            if "year" in file_doc["metadata"]:
                available_years.add(file_doc["metadata"]["year"])
            if "module" in file_doc["metadata"]:
                available_modules.add(file_doc["metadata"]["module"])
    
    # Get distinct values from MongoDB collections too
    for resource in resources:
        if "course" in resource:
            available_courses.add(resource["course"])
        if "year" in resource:
            available_years.add(resource["year"])
        if "module" in resource:
            available_modules.add(resource["module"])
            
    for note in notes:
        if "course" in note:
            available_courses.add(note["course"])
        if "year" in note:
            available_years.add(note["year"])
        if "module" in note:
            available_modules.add(note["module"])
    
    return {
        "summary": {
            "resources_count": len(resources),
            "notes_count": len(notes),
            "gridfs_files_count": len(gridfs_files),
            "metadata_statistics": metadata_counts,
            "available_courses": sorted(list(available_courses)),
            "available_years": sorted(list(available_years)),
            "available_modules": sorted(list(available_modules))
        },
        "resources": resources,
        "notes": notes,
        "gridfs_files": gridfs_files
    }

if __name__ == "__main__":
    app.run(debug=True)
