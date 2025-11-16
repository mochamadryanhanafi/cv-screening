from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UploadedFileSerializer, EvaluationJobSerializer, EvaluationRequestSerializer
from .throttles import UploadThrottle, EvaluateThrottle, ResultThrottle
from core.domain.models import UploadedFile, EvaluationJob
from evaluations.tasks import evaluate_documents


class UploadView(generics.CreateAPIView):
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]
    # throttle_classes = [UploadThrottle]


class EvaluateView(generics.GenericAPIView):
    serializer_class = EvaluationRequestSerializer
    permission_classes = [IsAuthenticated]
    # throttle_classes = [EvaluateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            cv_id = serializer.validated_data['cv_id']
            project_report_id = serializer.validated_data['project_report_id']

            try:
                UploadedFile.objects.get(id=cv_id)
                UploadedFile.objects.get(id=project_report_id)
            except UploadedFile.DoesNotExist:
                return Response({'error': 'One or more files not found'}, status=status.HTTP_404_NOT_FOUND)

            job = EvaluationJob.objects.create(
                job_title=serializer.validated_data['job_title'],
                cv_id=cv_id,
                project_report_id=project_report_id,
            )

            evaluate_documents.delay(str(job.id))

            return Response({'id': str(job.id), 'status': job.status, 'message': 'Evaluation queued successfully'}, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResultView(generics.RetrieveAPIView):
    queryset = EvaluationJob.objects.all()
    serializer_class = EvaluationJobSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'job_id'
    permission_classes = [IsAuthenticated]
    # throttle_classes = [ResultThrottle] # Throttles are currently disabled

    def get_object(self):
        obj = super().get_object()
        obj.refresh_from_db() # Force refresh from database
        return obj