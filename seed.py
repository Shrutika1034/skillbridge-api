"""
Database seeding script
Creates test data: 2 institutions, 4 trainers, 15 students, 3 batches, 8 sessions, and attendance records
"""
import sys
from datetime import datetime, timedelta
import secrets

from src.database import SessionLocal, Base, engine
from src.database import (
    User as UserDB, Institution as InstitutionDB, 
    Batch as BatchDB, Session as SessionDB, 
    Attendance as AttendanceDB, BatchInvite as BatchInviteDB,
    RoleEnum, AttendanceStatusEnum
)
from src.auth import hash_password

def seed_database():
    """Populate database with test data"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(UserDB).count() > 0:
            print("Database already seeded. Skipping...")
            return
        
        print("Starting database seeding...")
        
        # Create institutions
        inst1 = InstitutionDB(name="Tech Academy")
        inst2 = InstitutionDB(name="Skills Hub")
        db.add_all([inst1, inst2])
        db.flush()

        # Create institutions (users with institution role)
        institution1 = UserDB(
            name="Tech Academy Admin",
            email="admin@techacademy.org",
            hashed_password=hash_password("password123"),
            role=RoleEnum.INSTITUTION,
            institution_id=inst1.id
        )
        
        institution2 = UserDB(
            name="Skills Hub Admin",
            email="admin@skillshub.org",
            hashed_password=hash_password("password123"),
            role=RoleEnum.INSTITUTION,
            institution_id=inst2.id
        )
        
        db.add_all([institution1, institution2])
        db.flush()  # Flush to get IDs
        
        print(f"✓ Created 2 institutions")
        
        # Create trainers
        trainer_emails = [
            "trainer1@techacademy.org",
            "trainer2@techacademy.org",
            "trainer3@skillshub.org",
            "trainer4@skillshub.org"
        ]
        
        trainers = []
        for i, email in enumerate(trainer_emails):
            trainer = UserDB(
                name=f"Trainer {i+1}",
                email=email,
                hashed_password=hash_password("password123"),
                role=RoleEnum.TRAINER,
                institution_id=inst1.id if i < 2 else inst2.id
            )
            trainers.append(trainer)
            db.add(trainer)
        
        db.flush()
        print(f"✓ Created 4 trainers")
        
        # Create students
        students = []
        for i in range(15):
            institution_id = inst1.id if i < 8 else inst2.id
            student = UserDB(
                name=f"Student {i+1}",
                email=f"student{i+1}@example.com",
                hashed_password=hash_password("password123"),
                role=RoleEnum.STUDENT,
                institution_id=institution_id
            )
            students.append(student)
            db.add(student)
        
        db.flush()
        print(f"✓ Created 15 students")
        
        # Create programme manager
        pm = UserDB(
            name="Programme Manager",
            email="pm@skillbridge.org",
            hashed_password=hash_password("password123"),
            role=RoleEnum.PROGRAMME_MANAGER
        )
        db.add(pm)
        
        # Create monitoring officer
        mo = UserDB(
            name="Monitoring Officer",
            email="monitoring@skillbridge.org",
            hashed_password=hash_password("password123"),
            role=RoleEnum.MONITORING_OFFICER
        )
        db.add(mo)
        db.flush()
        
        print(f"✓ Created Programme Manager and Monitoring Officer")
        
        # Create batches
        batch1 = BatchDB(
            name="Python Basics - Batch A",
            institution_id=inst1.id,
            created_by_id=trainers[0].id
        )
        
        batch2 = BatchDB(
            name="Web Development - Batch B",
            institution_id=inst2.id,
            created_by_id=trainers[2].id
        )
        
        batch3 = BatchDB(
            name="Data Science - Batch C",
            institution_id=inst1.id,
            created_by_id=trainers[1].id
        )
        
        db.add_all([batch1, batch2, batch3])
        db.flush()
        
        print(f"✓ Created 3 batches")
        
        # Assign trainers to batches
        batch1.trainers.extend([trainers[0], trainers[1]])
        batch2.trainers.extend([trainers[2], trainers[3]])
        batch3.trainers.append(trainers[1])
        
        # Assign students to batches
        batch1.students.extend(students[0:6])
        batch2.students.extend(students[6:12])
        batch3.students.extend(students[12:15])
        
        db.flush()
        print(f"✓ Assigned trainers and students to batches")
        
        # Create sessions
        sessions = []
        base_date = datetime.utcnow().date()
        
        # Batch 1 sessions
        for i in range(3):
            session = SessionDB(
                batch_id=batch1.id,
                trainer_id=trainers[0].id,
                title=f"Python Basics - Session {i+1}",
                date=str(base_date - timedelta(days=3-i)),
                start_time="10:00",
                end_time="12:00"
            )
            sessions.append(session)
            db.add(session)
        
        # Batch 2 sessions
        for i in range(3):
            session = SessionDB(
                batch_id=batch2.id,
                trainer_id=trainers[2].id,
                title=f"Web Development - Session {i+1}",
                date=str(base_date - timedelta(days=2-i)),
                start_time="14:00",
                end_time="16:00"
            )
            sessions.append(session)
            db.add(session)
        
        # Batch 3 sessions
        for i in range(2):
            session = SessionDB(
                batch_id=batch3.id,
                trainer_id=trainers[1].id,
                title=f"Data Science - Session {i+1}",
                date=str(base_date - timedelta(days=1-i)),
                start_time="09:00",
                end_time="11:00"
            )
            sessions.append(session)
            db.add(session)
        
        db.flush()
        print(f"✓ Created 8 sessions")
        
        # Create attendance records
        # For batch1 sessions
        for session in sessions[0:3]:
            for student in batch1.students:
                status = [AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.ABSENT, 
                         AttendanceStatusEnum.LATE][int(student.id) % 3]
                attendance = AttendanceDB(
                    session_id=session.id,
                    student_id=student.id,
                    status=status
                )
                db.add(attendance)
        
        # For batch2 sessions
        for session in sessions[3:6]:
            for student in batch2.students:
                status = [AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.PRESENT,
                         AttendanceStatusEnum.ABSENT][int(student.id) % 3]
                attendance = AttendanceDB(
                    session_id=session.id,
                    student_id=student.id,
                    status=status
                )
                db.add(attendance)
        
        # For batch3 sessions
        for session in sessions[6:8]:
            for student in batch3.students:
                status = AttendanceStatusEnum.PRESENT if int(student.id) % 2 == 0 else AttendanceStatusEnum.ABSENT
                attendance = AttendanceDB(
                    session_id=session.id,
                    student_id=student.id,
                    status=status
                )
                db.add(attendance)
        
        db.flush()
        print(f"✓ Created attendance records for all sessions")
        
        # Create some batch invites
        invite1 = BatchInviteDB(
            batch_id=batch1.id,
            token=secrets.token_urlsafe(32),
            created_by_id=trainers[0].id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            used=False
        )
        
        invite2 = BatchInviteDB(
            batch_id=batch2.id,
            token=secrets.token_urlsafe(32),
            created_by_id=trainers[2].id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            used=False
        )
        
        db.add_all([invite1, invite2])
        db.flush()
        print(f"✓ Created batch invites")
        
        # Commit all changes
        db.commit()
        
        print("\n" + "="*60)
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nTest Accounts:")
        print("-" * 60)
        print(f"Institution 1: admin@techacademy.org / password123")
        print(f"Institution 2: admin@skillshub.org / password123")
        print(f"Trainer 1: trainer1@techacademy.org / password123")
        print(f"Trainer 2: trainer2@techacademy.org / password123")
        print(f"Trainer 3: trainer3@skillshub.org / password123")
        print(f"Trainer 4: trainer4@skillshub.org / password123")
        print(f"Student 1: student1@example.com / password123")
        print(f"Student 8: student8@example.com / password123")
        print(f"Programme Manager: pm@skillbridge.org / password123")
        print(f"Monitoring Officer: monitoring@skillbridge.org / password123")
        print("-" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
