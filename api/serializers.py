from rest_framework import serializers
from core.domain.models import UploadedFile, EvaluationJob

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'file', 'uploaded_at']

    def validate_file(self, value):
        # Validate file type
        if value.content_type != 'application/pdf':
            raise serializers.ValidationError("Only PDF files are allowed.")
        
        # Validate file size (e.g., 10MB limit)
        ten_mb = 10 * 1024 * 1024
        if value.size > ten_mb:
            raise serializers.ValidationError(f"File size cannot exceed {ten_mb / 1024 / 1024}MB.")
            
        return value

class EvaluationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationJob
        fields = '__all__'

class EvaluationRequestSerializer(serializers.Serializer):
    job_title = serializers.CharField(max_length=255)
    cv_id = serializers.UUIDField()
    project_report_id = serializers.UUIDField()
