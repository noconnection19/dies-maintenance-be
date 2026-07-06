"""Router untuk Dies Preventive."""
from app.routers.dies_task import make_dies_router
from app.models.dies_task import TaskType

router = make_dies_router(TaskType.PREVENTIVE)
