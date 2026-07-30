"""
Fungsi internal/admin yang dijalankan saat startup.

Tidak diekspos sebagai endpoint publik.
"""
import os
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.dies_task import Line, Machine, Die


def seed_admin(db: Session) -> None:
    """Create default admin user if users table is empty."""
    if db.query(User).count() == 0:
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        admin = User(
            username="admin",
            full_name="Administrator",
            role="Admin",
            hashed_password=hash_password(admin_pass),
        )
        db.add(admin)
        db.commit()
        print(f"[SEED] Seeded initial admin account (username: admin)")
        if admin_pass == "admin123":
            print("[WARNING] Using default password 'admin123'. Change it after initial login or set ADMIN_PASSWORD in environment.")


    # Seed default lines
    if db.query(Line).count() == 0:
        lines = [
            Line(line_cd="TR-01", line_name="Tandem Press Line 1"),
            Line(line_cd="TR-02", line_name="Tandem Press Line 2"),
            Line(line_cd="TR-03", line_name="Tandem Press Line 3"),
        ]
        db.add_all(lines)
        db.commit()
        print("[SEED] Seeded default lines")

    # Seed default machines
    if db.query(Machine).count() == 0:
        machines = [
            Machine(machine_cd="TR1", line_cd="TR-01", machine_name="Tandem 1"),
            Machine(machine_cd="TR2", line_cd="TR-01", machine_name="Tandem 2"),
            Machine(machine_cd="TD", line_cd="TR-01", machine_name="TD Machine"),
            Machine(machine_cd="TR1_L2", line_cd="TR-02", machine_name="Tandem 1 L2"),
            Machine(machine_cd="TD_L2", line_cd="TR-02", machine_name="TD Machine L2"),
            Machine(machine_cd="TD_L3", line_cd="TR-03", machine_name="TD Machine L3"),
        ]
        db.add_all(machines)
        db.commit()
        print("[SEED] Seeded default machines")

    # Seed default dies
    if db.query(Die).count() == 0:
        dies = [
            Die(part_no="47781.2-0K090", model="660A"),
            Die(part_no="47781.2-0K241", model="650A"),
            Die(part_no="48733-0K010", model="699N"),
            Die(part_no="51161.2-KK010", model="660A"),
            Die(part_no="52301-0K070", model="650A"),
            Die(part_no="55410-0K010", model="699N"),
            Die(part_no="65900-0K010", model="660A"),
        ]
        db.add_all(dies)
        db.commit()
        print("[SEED] Seeded default dies")

    # Seed default dies operations from TEMP_TR1_PCS_M and TEMP_TR2_PCS_M
    from app.models.dies_task import DiesOperation
    if db.query(DiesOperation).count() == 0:
        from sqlalchemy import text
        try:
            # We seed from TEMP_TR1_PCS_M for machine '1200'
            tr1_data = db.execute(text("SELECT DISTINCT PART_NO, OP, PROSES FROM TEMP_TR1_PCS_M")).all()
            for row in tr1_data:
                part_exists = db.query(Die).filter_by(part_no=row[0]).first() is not None
                machine_exists = db.query(Machine).filter_by(machine_cd="1200").first() is not None
                if part_exists and machine_exists:
                    op = DiesOperation(part_no=row[0], machine_cd="1200", op=row[1], proses=row[2])
                    db.add(op)
            
            # We seed from TEMP_TR2_PCS_M for machine '1600'
            tr2_data = db.execute(text("SELECT DISTINCT PART_NO, OP, PROSES FROM TEMP_TR2_PCS_M")).all()
            for row in tr2_data:
                part_exists = db.query(Die).filter_by(part_no=row[0]).first() is not None
                machine_exists = db.query(Machine).filter_by(machine_cd="1600").first() is not None
                if part_exists and machine_exists:
                    op = DiesOperation(part_no=row[0], machine_cd="1600", op=row[1], proses=row[2])
                    db.add(op)
            
            db.commit()
            print("[SEED] Seeded dies operations from TEMP_TR1_PCS_M and TEMP_TR2_PCS_M")
        except Exception as e:
            db.rollback()
            print(f"[SEED] Failed to seed dies operations: {e}")
