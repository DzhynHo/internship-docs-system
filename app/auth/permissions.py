"""
Decoratory do kontroli dostępu na podstawie ról (RBAC).
"""

from functools import wraps
from flask import abort
from flask_login import current_user
from flask_login import login_required


def role_required(*required_roles):
    """
    Decorator: Sprawdza czy użytkownik ma jedną z wymaganych ról.
    
    Przykład:
        @role_required("student", "opiekun")
        def view_dashboard():
            return "OK"
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in required_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator: Wymaga roli 'admin'"""
    return role_required("admin")(f)


def student_required(f):
    """Decorator: Wymaga roli 'student'"""
    return role_required("student")(f)


def mentor_required(f):
    """Decorator: Wymaga roli 'opiekun'"""
    return role_required("opiekun")(f)


def staff_required(f):
    """Decorator: Wymaga roli 'staff' lub 'admin'"""
    return role_required("staff", "admin")(f)


def check_resource_access(resource_id_param="id"):
    """
    Decorator: Sprawdza dostęp do zasobu na poziomie rekordu (Row-Level Security).
    
    Przykład:
        @check_resource_access("internship_id")
        def view_internship(internship_id):
            internship = Internship.query.get(internship_id)
            return render_template("view.html", internship=internship)
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            from app.models.internship import Internship
            
            # Pobierz ID zasobu z parametrów
            resource_id = kwargs.get(resource_id_param)
            if not resource_id:
                abort(400, "Missing resource ID")
            
            internship = Internship.query.get(resource_id)
            if not internship:
                abort(404)
            
            # Sprawdzenie uprawnień w zależności od roli
            if current_user.role == "student":
                # Student może przejrzeć TYLKO swoją praktykę
                if internship.student_id != current_user.id:
                    abort(403)
            
            elif current_user.role == "opiekun":
                # Opiekun może przejrzeć praktyki swoich studentów
                if internship.mentor_id != current_user.id:
                    abort(403)
            
            elif current_user.role == "staff":
                # Sekretariat widzi wszystko (RO)
                pass
            
            elif current_user.role == "admin":
                # Admin ma pełny dostęp
                pass
            
            else:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_document_access(f):
    """
    Decorator: Sprawdza dostęp do dokumentu (DocumentSubmission).
    
    Przejmuje document_id z kwargs.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        from app.models import DocumentSubmission
        
        document_id = kwargs.get("document_id")
        if not document_id:
            abort(400, "Missing document ID")
        
        document = DocumentSubmission.query.get(document_id)
        if not document:
            abort(404)
        
        # Logika dostępu
        if current_user.role == "student":
            # Student może przejrzeć TYLKO swoje dokumenty
            if document.user_id != current_user.id:
                abort(403)
        
        elif current_user.role == "opiekun":
            # Opiekun może przejrzeć dokumenty swoich studentów
            if document.internship and document.internship.mentor_id != current_user.id:
                abort(403)
        
        elif current_user.role == "staff":
            # Sekretariat widzi wszystko
            pass
        
        elif current_user.role == "admin":
            # Admin ma pełny dostęp
            pass
        
        else:
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def check_protocol_access(f):
    """
    Decorator: Specjalna kontrola dostępu dla Protokołu (Załącznik 8).
    
    Tylko Sekretariat i Dyrekcja mogą widzieć Protokół!
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role not in ["staff", "admin"]:
            abort(403, "Brak dostępu do Protokołu. Tylko Sekretariat i Dyrekcja.")
        
        return f(*args, **kwargs)
    return decorated_function


def check_approval_permission(approval_level="mentor"):
    """
    Decorator: Sprawdza uprawnienia do zatwierdzania dokumentu.
    
    approval_level:
        - "mentor": Opiekun może zatwierdzić
        - "director": Tylko Admin/Dyrekcja
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if approval_level == "mentor":
                if current_user.role not in ["opiekun", "admin", "staff"]:
                    abort(403, "Tylko opiekun i wyżsi mogą zatwierdzić")
            
            elif approval_level == "director":
                if current_user.role != "admin":
                    abort(403, "Tylko dyrekcja może zatwierdzić na tym poziomie")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Funkcje do sprawdzania uprawnień (mogą być używane w szablonach)

def can_edit_document(user, document):
    """Sprawdza czy użytkownik może edytować dokument."""
    if document.status != "draft":
        return False
    
    if user.role == "student":
        return document.user_id == user.id
    
    return user.role in ["admin", "staff"]


def can_approve_document(user, document):
    """Sprawdza czy użytkownik może zatwierdzić dokument."""
    if user.role == "opiekun":
        # Opiekun tylko swoich studentów
        return document.internship and document.internship.mentor_id == user.id
    
    if user.role in ["admin", "staff"]:
        return True
    
    return False


def can_view_protocol(user):
    """Sprawdza czy użytkownik może widzieć Protokół (załącznik 8)."""
    return user.role in ["admin", "staff"]


def can_view_internship(user, internship):
    """Sprawdza czy użytkownik może widzieć praktykę."""
    if user.role == "student":
        return internship.student_id == user.id
    
    if user.role == "opiekun":
        return internship.mentor_id == user.id
    
    if user.role in ["admin", "staff"]:
        return True
    
    return False
