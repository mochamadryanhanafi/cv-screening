from rest_framework import serializers
from core.domain.models import UploadedFile, EvaluationJob

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'file', 'uploaded_at']

class EvaluationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationJob
        fields = '__all__'

class EvaluationRequestSerializer(serializers.Serializer):
    job_title = serializers.CharField(max_length=255)
    cv_id = serializers.UUIDField()
    project_report_id = serializers.UUIDField()
