from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from . import services


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_summary(request: Request) -> Response:
    return Response(services.summary(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_per_status(request: Request) -> Response:
    return Response(services.per_status(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_per_source(request: Request) -> Response:
    return Response(services.per_source(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_weekly(request: Request) -> Response:
    weeks = max(1, min(int(request.query_params.get("weeks", 12)), 52))
    return Response(services.weekly_volume(request.user, weeks=weeks))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_funnel(request: Request) -> Response:
    return Response(services.funnel(request.user))
