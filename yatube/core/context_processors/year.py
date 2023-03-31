from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    return {"year": timezone.datetime.now().year}
