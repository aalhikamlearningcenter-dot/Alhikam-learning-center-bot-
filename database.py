students = {}

def add_student(user_id, data):
    students[user_id] = data

def get_student(user_id):
    return students.get(user_id)

def payment_verified(user_id):
    if user_id in students:
        students[user_id]["verified"] = True