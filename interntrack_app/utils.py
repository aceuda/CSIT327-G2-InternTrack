def normalize_student_data(data):
    return {
        "year_level": data.get("year_level", "").strip().title(),  # e.g., "3rd Year"
        "program": data.get("program", "").strip().upper(),          # BSIT
        "student_id": data.get("student_id"),                         # 18-0668-202
         #"status": data.get("status", "").strip().title()  
    }

def normalize_admin_data(data):
    return {
        "department": data.get("department", "").strip().title(),  # e.g., "Human Resources"
        "position": data.get("position", "").strip().title(),      # e.g., "Team Lead"
        "employee_id": data.get("employee_id", ""),
    }