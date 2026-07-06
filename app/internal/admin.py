"""
Fungsi internal/admin yang dijalankan saat startup.

Tidak diekspos sebagai endpoint publik.
"""
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.dies_task import Line, Machine, Die


def seed_admin(db: Session) -> None:
    """Buat akun admin default jika tabel users masih kosong."""
    if db.query(User).count() == 0:
        admin = User(
            username="admin",
            full_name="Administrator",
            role="Admin",
            hashed_password=hash_password("admin123"),
        )
        db.add(admin)
        db.commit()
        print("[SEED] Seeded default admin  (username: admin / password: admin123)")
        print("[WARNING] Segera ganti password default setelah login pertama!")

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
