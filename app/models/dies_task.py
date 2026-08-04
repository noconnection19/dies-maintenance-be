"""Model database untuk Dies Task, Master Data, Transaksi, dan History (100% ERD v3 Spec)."""
import enum
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, ForeignKey, Date
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func

from app.db.database import Base


class TaskType(str, enum.Enum):
    LINE_STOP  = "LINE_STOP"
    REPAIR     = "REPAIR"
    PREVENTIVE = "PREVENTIVE"


class MstrCompany(Base):
    __tablename__ = "MSTR_COMPANY"

    company_cd   = Column("COMPANY_CD", String(10), primary_key=True)
    plant_cd     = Column("PLANT_CD", String(10), primary_key=True)
    company_name = Column("COMPANY_NAME", String(100), nullable=True)


class MstrPlant(Base):
    __tablename__ = "MSTR_PLANT"

    plant_cd   = Column("PLANT_CD", String(100), primary_key=True)
    plant_name = Column("PLANT_NAME", String(100), nullable=True)


class Line(Base):
    __tablename__ = "MSTR_LINE"

    line_cd    = Column("LINE_CD", String(100), primary_key=True, index=True)
    company_cd = Column("COMPANY_CD", String(10), nullable=True)
    plant_cd   = Column("PLANT_CD", String(10), nullable=True)
    line_name  = Column("LINE_NAME", String(100), nullable=False)


class Machine(Base):
    __tablename__ = "MSTR_MACHINE"

    machine_cd   = Column("MACHINE_CD", String(100), primary_key=True, index=True)
    line_cd      = Column("LINE_CD", String(100), ForeignKey("MSTR_LINE.LINE_CD"), nullable=True)
    company_cd   = Column("COMPANY_CD", String(10), nullable=True)
    plant_cd     = Column("PLANT_CD", String(10), nullable=True)
    machine_name = Column("MACHINE_NAME", String(100), nullable=False)

    line = relationship("Line")


class Die(Base):
    __tablename__ = "MSTR_DIES"

    part_no       = Column("PART_NO", String(100), primary_key=True, index=True)
    company_cd    = Column("COMPANY_CD", String(10), nullable=True)
    plant_cd      = Column("PLANT_CD", String(10), nullable=True)
    part_name     = Column("PART_NAME", String(200), nullable=True)
    part_image_id = Column("PART_IMAGE_ID", BigInteger, nullable=True)

    @property
    def model(self):
        return self.part_name or self.part_no


class MstrModel(Base):
    __tablename__ = "MSTR_MODEL"

    model      = Column("MODEL", String(10), primary_key=True)
    model_name = Column("MODEL_NAME", String(200), nullable=True)


class MstrDiesModel(Base):
    __tablename__ = "MSTR_DIES_MODEL"

    part_no = Column("PART_NO", String(100), primary_key=True)
    model   = Column("MODEL", String(10), primary_key=True)


class DiesOperation(Base):
    __tablename__ = "MSTR_DIES_OPERATION"

    part_no      = Column("PART_NO", String(100), primary_key=True)
    process_seq  = Column("PROCESS_SEQ", String(100), primary_key=True)
    machine_cd   = Column("MACHINE_CD", String(100), primary_key=True)
    company_cd   = Column("COMPANY_CD", String(10), primary_key=True)
    plant_cd     = Column("PLANT_CD", String(10), primary_key=True)
    process_name = Column("PROCESS_NAME", String(100), nullable=True)

    @property
    def operation_seq(self):
        return self.process_seq

    @property
    def operation_name(self):
        return self.process_name or self.process_seq

    @property
    def op(self):
        return self.process_seq

    @property
    def proses(self):
        return self.process_name or self.process_seq


class Attachment(Base):
    __tablename__ = "DET_ATTACHMENT"

    id              = Column("ATTACHMENT_ID", BigInteger, primary_key=True, autoincrement=True)
    attachment_name = Column("ATTACHMENT_NAME", String(255), nullable=False)
    mimetype        = Column("MIMETYPE", String(100), nullable=True)
    size            = Column("SIZE", BigInteger, nullable=True)
    file_path       = Column("FILE_PATH", String(500), nullable=False)


class DiesTask(Base):
    """
    Mapped directly to DET_DIES_LINE_STOP to fetch and save real Line Stop data.
    """
    __tablename__ = "DET_DIES_LINE_STOP"

    id                      = Column("DIES_LINE_STOP_ID", String(100), primary_key=True, index=True)
    part_no                 = Column("PART_NO", String(100), ForeignKey("MSTR_DIES.PART_NO"), nullable=True)
    operation_seq           = Column("OPERATION_SEQ", String(100), nullable=True)
    machine_cd              = Column("MACHINE_CD", String(100), ForeignKey("MSTR_MACHINE.MACHINE_CD"), nullable=True)
    line_cd                 = Column("LINE_CD", String(100), ForeignKey("MSTR_LINE.LINE_CD"), nullable=True)
    company_cd              = Column("COMPANY_CD", String(10), nullable=True)
    plant_cd                = Column("PLANT_CD", String(10), nullable=True)
    approval_id             = Column("APPROVAL_ID", String(100), nullable=True)
    documentation_before_id = Column("DOCUMENTATION_BEFORE_ID", BigInteger, ForeignKey("DET_ATTACHMENT.ATTACHMENT_ID"), nullable=True)
    documentation_after_id  = Column("DOCUMENTATION_AFTER_ID", BigInteger, ForeignKey("DET_ATTACHMENT.ATTACHMENT_ID"), nullable=True)

    model          = Column("MODEL", String(10), nullable=True)
    shift          = Column("SHIFT", String(1), nullable=True)
    classification = Column("CLASSIFICATION", String(100), nullable=True)
    _status        = Column("STATUS", String(2), nullable=True)

    duration_ls = Column("DURATION_LS", Integer, nullable=True)
    duration_mh = Column("DURATION_MH", Integer, nullable=True)
    repaired_dt = Column("REPAIRED_DT", DateTime, nullable=True)
    repaired_by = Column("REPAIRED_BY", String(50), nullable=True)

    problem_cd     = Column("PROBLEM_CD", String(10), nullable=True)
    problem        = Column("PROBLEM", String(200), nullable=True)
    sub_problem    = Column("SUB_PROBLEM", String(200), nullable=True)
    rootcause      = Column("ROOTCAUSE", String(200), nullable=True)
    countermeasure = Column("COUNTERMEASURE", String(200), nullable=True)
    remark         = Column("REMARK", String(200), nullable=True)

    created_by = Column("CREATED_BY", String(100), nullable=True)
    created_dt = Column("CREATED_DT", DateTime, server_default=func.now())
    changed_by = Column("CHANGED_BY", String(100), nullable=True)
    changed_dt = Column("CHANGED_DT", DateTime, onupdate=func.now())

    @hybrid_property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @status.expression
    def status(cls):
        return cls._status

    # Relationships
    line                 = relationship("Line")
    machine              = relationship("Machine")
    die                  = relationship("Die")
    documentation_before = relationship("Attachment", foreign_keys=[documentation_before_id])
    documentation_after  = relationship("Attachment", foreign_keys=[documentation_after_id])
    part_orders          = relationship("PartOrderHeader", backref="task", cascade="all, delete-orphan")
    pics                 = relationship(
        "DetDiesPic",
        primaryjoin="DiesTask.id == foreign(DetDiesPic.dies_reff_id)",
        viewonly=True,
    )

    @property
    def pic_usernames(self):
        return list(dict.fromkeys(p.username for p in self.pics if p.username))



class DetFormDiesRepair(Base):
    __tablename__ = "DET_FORM_DIES_REPAIR"

    form_dies_repair_id = Column("FORM_DIES_REPAIR_ID", String(100), primary_key=True)
    dies_line_stop_id   = Column("DIES_LINE_STOP_ID", String(100), ForeignKey("DET_DIES_LINE_STOP.DIES_LINE_STOP_ID"), nullable=True)
    pic                 = Column("PIC", String(100), nullable=True)
    status              = Column("STATUS", String(100), nullable=True)
    created_dt          = Column("CREATED_DT", DateTime, server_default=func.now())
    created_by          = Column("CREATED_BY", String(50), nullable=True)


class DetDiesRepair(Base):
    __tablename__ = "DET_DIES_REPAIR"

    dies_repair_id = Column("DIES_REPAIR_ID", String(100), primary_key=True)
    part_no        = Column("PART_NO", String(100), nullable=True)
    operation_seq  = Column("OPERATION_SEQ", String(100), nullable=True)
    repaired_dt    = Column("REPAIRED_DT", DateTime, nullable=True)
    repaired_by    = Column("REPAIRED_BY", String(50), nullable=True)


class DetDiesPic(Base):
    __tablename__ = "DET_DIES_PIC"

    dies_pic_id   = Column("DIES_PIC_ID", Integer, primary_key=True, autoincrement=True)
    dies_reff_id  = Column("DIES_REFF_ID", String(100), nullable=False)
    username      = Column("USERNAME", String(50), nullable=False)
    is_origin_pic = Column("IS_ORIGIN_PIC", Integer, nullable=True)
    created_by    = Column("CREATED_BY", String(100), nullable=True)
    created_dt    = Column("CREATED_DT", DateTime, nullable=True)
    changed_by    = Column("CHANGED_BY", String(100), nullable=True)
    changed_dt    = Column("CHANGED_DT", DateTime, nullable=True)


class PartOrderHeader(Base):
    __tablename__ = "DET_PART_ORDER_H"

    id           = Column("PART_ORDER_ID", String(100), primary_key=True)
    dies_reff_id = Column("DIES_REFF_ID", String(100), ForeignKey("DET_DIES_LINE_STOP.DIES_LINE_STOP_ID"), nullable=False)
    status       = Column("STATUS", String(50), default="Waiting Confirmation")

    details = relationship("PartOrderDetail", back_populates="header", cascade="all, delete-orphan")


class PartOrderDetail(Base):
    __tablename__ = "DET_PART_ORDER_D"

    part_order_id = Column("PART_ORDER_ID", String(100), ForeignKey("DET_PART_ORDER_H.PART_ORDER_ID"), primary_key=True)
    item_no       = Column("ITEM_NO", Integer, primary_key=True)
    part_cd       = Column("PART_CD", String(100), nullable=False)
    part_name     = Column("PART_NAME", String(100), nullable=False)
    location      = Column("LOCATION", String(100), nullable=True)
    qty           = Column("QTY", Integer, default=1)

    header = relationship("PartOrderHeader", back_populates="details")


class MstrPartLocation(Base):
    __tablename__ = "MSTR_PART_LOCATION"

    location_cd   = Column("LOCATION_CD", String(100), primary_key=True)
    location_name = Column("LOCATION_NAME", String(100), nullable=True)


class MstrSparepart(Base):
    __tablename__ = "MSTR_SPAREPART"

    part_cd     = Column("PART_CD", String(100), primary_key=True)
    location_cd = Column("LOCATION_CD", String(100), nullable=True)
    part_name   = Column("PART_NAME", String(100), nullable=True)
    qty_stock   = Column("QTY_STOCK", Integer, default=0)


class MstrApprovalH(Base):
    __tablename__ = "MSTR_APPROVAL_H"

    approval_cd = Column("APPROVAL_CD", String(50), primary_key=True)


class MstrApprovalD(Base):
    __tablename__ = "MSTR_APPROVAL_D"

    approval_d_id = Column("APPROVAL_D_ID", String(50), primary_key=True)
    approval_cd   = Column("APPROVAL_CD", String(50), nullable=True)
    role_cd       = Column("ROLE_CD", String(50), nullable=True)
    level         = Column("LEVEL", Integer, nullable=True)


class DetApproval(Base):
    __tablename__ = "DET_APPROVAL"

    approval_r_id   = Column("APPROVAL_R_ID", String(100), primary_key=True)
    reff_id         = Column("REFF_ID", String(100), nullable=True)
    approval_d_id   = Column("APPROVAL_D_ID", String(50), nullable=True)
    username        = Column("USERNAME", String(100), nullable=True)
    version_no      = Column("VERSION_NO", Integer, nullable=True)
    approval_status = Column("APPROVAL_STATUS", String(50), nullable=True)


class MstrPreventiveFormH(Base):
    __tablename__ = "MSTR_PREVENTIVE_FORM_H"

    form_type     = Column("FORM_TYPE", String(100), primary_key=True)
    part_no       = Column("PART_NO", String(100), primary_key=True)
    operation_seq = Column("OPERATION_SEQ", String(100), primary_key=True)


class MstrPreventiveFormD(Base):
    __tablename__ = "MSTR_PREVENTIVE_FORM_D"

    form_type     = Column("FORM_TYPE", String(100), primary_key=True)
    part_no       = Column("PART_NO", String(100), primary_key=True)
    operation_seq = Column("OPERATION_SEQ", String(100), primary_key=True)
    item_id       = Column("ITEM_ID", String(100), primary_key=True)
    item_name     = Column("ITEM_NAME", String(100), nullable=True)
    sub_item      = Column("SUB_ITEM", String(100), nullable=True)
    check_point   = Column("CHECK_POINT", String(100), nullable=True)
    methode       = Column("METHODE", String(100), nullable=True)


class DetDiesPreventiveScheduleH(Base):
    __tablename__ = "DET_DIES_PREVENTIVE_SCHEDULE_H"

    dies_preventive_h_id = Column("DIES_PREVENTIVE_H_ID", String(100), primary_key=True)
    part_no              = Column("PART_NO", String(100), nullable=True)
    operation_seq        = Column("OPERATION_SEQ", String(100), nullable=True)
    register_date        = Column("REGISTER_DATE", Date, nullable=True)


class DetDiesPreventiveScheduleD(Base):
    __tablename__ = "DET_DIES_PREVENTIVE_SCHEDULE_D"

    dies_preventive_d_id = Column("DIES_PREVENTIVE_D_ID", String(100), primary_key=True)
    dies_preventive_h_id = Column("DIES_PREVENTIVE_H_ID", String(100), nullable=True)
    part_no              = Column("PART_NO", String(100), nullable=True)
    operation_seq        = Column("OPERATION_SEQ", String(100), nullable=True)
    target_date          = Column("TARGET_DATE", Date, nullable=True)


class DetPreventiveForm(Base):
    __tablename__ = "DET_PREVENTIVE_FORM"

    preventive_form_id   = Column("PREVENTIVE_FORM_ID", String(100), primary_key=True)
    dies_preventive_d_id = Column("DIES_PREVENTIVE_D_ID", String(100), nullable=True)


class MstrSystem(Base):
    __tablename__ = "MSTR_SYSTEM"

    system_type  = Column("SYSTEM_TYPE", String(100), primary_key=True)
    system_cd    = Column("SYSTEM_CD", String(100), primary_key=True)
    system_value = Column("SYSTEM_VALUE", String(400), nullable=False)
    remark       = Column("REMARK", String(400), nullable=True)
    created_by   = Column("CREATED_BY", String(100), nullable=True)
    created_dt   = Column("CREATED_DT", DateTime, nullable=True)
    changed_by   = Column("CHANGED_BY", String(100), nullable=True)
    changed_dt   = Column("CHANGED_DT", DateTime, nullable=True)

    @property
    def remarks(self):
        return self.remark


class HistLog(Base):
    __tablename__ = "HIST_LOG"

    log_id      = Column("LOG_ID", BigInteger, primary_key=True, autoincrement=True)
    api_url     = Column("API_URL", String(500), nullable=True)
    method      = Column("METHOD", String(10), nullable=True)
    param_body  = Column("PARAM_BODY", Text, nullable=True)
    param_query = Column("PARAM_QUERY", Text, nullable=True)
    response    = Column("RESPONSE", Text, nullable=True)
