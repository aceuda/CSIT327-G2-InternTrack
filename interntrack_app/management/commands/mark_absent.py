from django.core.management.base import BaseCommand
from django.utils import timezone
from interntrack_app.models import StudentProfile, Attendance
from datetime import datetime, time


class Command(BaseCommand):
    help = 'Automatically mark interns as absent if they have no time-in record during work hours (9AM - 5PM)'

    def handle(self, *args, **kwargs):
        now = timezone.localtime()
        today = now.date()
        current_time = now.time()
        
        # Work hours: 9AM to 5PM
        work_start = time(9, 0)  # 9:00 AM
        work_end = time(17, 0)   # 5:00 PM
        
        # Only mark absent after 5PM
        if current_time < work_end:
            self.stdout.write(
                self.style.WARNING(f'Current time is {current_time.strftime("%H:%M")}. Absent marking runs after 5:00 PM.')
            )
            return
        
        # Get all active students
        students = StudentProfile.objects.all()
        
        marked_count = 0
        
        for student in students:
            # Check if student has an attendance record for today
            attendance_record = Attendance.objects.filter(
                student=student,
                date=today
            ).first()
            
            # If no record exists OR both time_in and time_out are null, create/mark as absent
            if not attendance_record:
                # Create absent record
                Attendance.objects.create(
                    student=student,
                    date=today,
                    time_in=None,
                    time_out=None,
                    hours_rendered=0.00
                )
                marked_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Marked {student.full_name} as absent for {today}')
                )
            elif attendance_record.time_in is None and attendance_record.time_out is None:
                # Already has an absent record
                self.stdout.write(
                    self.style.WARNING(f'{student.full_name} already marked absent for {today}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal interns marked absent: {marked_count}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Absent marking completed at {current_time.strftime("%H:%M")}')
        )
