from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from core.domain.models import EvaluationJob
from evaluations.tasks import evaluate_documents

def home_view(request):
    return redirect("login")

def custom_404_view(request, exception=None):
    return render(request, "404.html", status=404)

def login_view(request):
    return render(request, "login.html")

@require_http_methods(["GET", "POST"])
def upload_cv_view(request):
    if request.method == "POST":
        cv_file = request.FILES.get("cv")
        if cv_file:
            evaluation = EvaluationJob.objects.create(cv=cv_file)
            evaluate_documents.delay(evaluation.id)
            return redirect("evaluation_result", evaluation_id=evaluation.id)
    return render(request, "upload.html")

def evaluation_result_view(request, evaluation_id):
    evaluation = EvaluationJob.objects.get(id=evaluation_id)
    return render(request, "evaluation_result.html", {"evaluation": evaluation})