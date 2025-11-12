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

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationJob
        fields = [
            'cv_match_rate', 
            'cv_feedback', 
            'project_score', 
            'project_feedback', 
            'overall_summary'
        ]

class EvaluationJobSerializer(serializers.ModelSerializer):
    result = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationJob
        fields = [
            'id', 
            'status', 
            'result', 
            'cv_match_rate', 
            'cv_feedback', 
            'project_score', 
            'project_feedback', 
            'overall_summary'
        ]
        read_only_fields = ['id', 'status', 'result']

    def get_result(self, obj):
        if obj.status == 'completed':
            return ResultSerializer(obj).data
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Remove individual result fields from the top-level representation
        # as they are now nested under 'result'.
        for field in ResultSerializer.Meta.fields:
            representation.pop(field, None)

        if instance.status in ['queued', 'processing']:
            # For queued or processing jobs, only show id and status
            return {
                'id': representation['id'],
                'status': representation['status']
            }
        
        if instance.status != 'completed':
            representation.pop('result', None)

        return representation


class EvaluationRequestSerializer(serializers.Serializer):
    job_title = serializers.CharField(max_length=255)
    cv_id = serializers.UUIDField()
    project_report_id = serializers.UUIDField()


class EvaluationRequestSerializer(serializers.Serializer):
    job_title = serializers.CharField(max_length=255)
    cv_id = serializers.UUIDField()
    project_report_id = serializers.UUIDField()
