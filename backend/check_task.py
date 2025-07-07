#!/usr/bin/env python3
import time
import sys
sys.path.append('.')
from app.core.celery_app import celery_app

task_id = '68b50eb4-f771-4c24-a2dd-ca16c6ccbb6b'
task = celery_app.AsyncResult(task_id)

for i in range(10):
    status = task.status
    print(f'Attempt {i+1}: Task status: {status}')
    if status != 'PENDING':
        print(f'Task info: {task.info}')
        break
    time.sleep(2)
else:
    print('Task still pending after 20 seconds')