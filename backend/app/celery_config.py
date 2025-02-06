from celery import Celery
from flask import current_app

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        task_track_started=True,
        task_always_eager=False,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        task_acks_late=True,
        include=['app.jobs']
    )
    
    class ContextTask(celery.Task):
        abstract = True
        
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
