from celery import Celery
from celery.schedules import crontab

# Create Celery instance
celery = Celery('app',
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0',
                include=['app.jobs'])

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
    task_acks_late=True
)

# Optional: Configure periodic tasks
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Daily reminders at 6 PM
    sender.add_periodic_task(
        crontab(hour=18, minute=0),
        'app.jobs.process_daily_reminders'
    )
    
    # Monthly reports on 1st of each month at 1 AM
    sender.add_periodic_task(
        crontab(hour=1, minute=0, day_of_month=1),
        'app.jobs.process_monthly_reports'
    )

if __name__ == '__main__':
    celery.start()
