"""Repository implementation for Phase 13 Pixel Office projections and activity feed."""

from typing import List, Optional, Any
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.office import (
    EmployeeVisualState,
    EmployeeWorkstationProjection,
    HumanAttentionItem,
    HumanAttentionType,
    OfficeActivityItem,
    OfficeAreaType,
)
from src.infrastructure.models.office_model import (
    HumanAttentionModel,
    OfficeActivityModel,
    OfficeWorkstationModel,
)


class GovernanceOfficeRepository:
    def __init__(self, session: Any):
        self._session = session

    def save_workstation(self, ws: EmployeeWorkstationProjection) -> EmployeeWorkstationProjection:
        model = OfficeWorkstationModel(
            employee_id=ws.employee_id,
            employee_name=ws.employee_name,
            employee_title=ws.employee_title,
            role=ws.role,
            department_id=ws.department_id,
            manager_id=ws.manager_id,
            desk_id=ws.desk_id,
            area_type=ws.area_type.value if hasattr(ws.area_type, "value") else str(ws.area_type),
            visual_state=ws.visual_state.value if hasattr(ws.visual_state, "value") else str(ws.visual_state),
            current_task_id=ws.current_task_id,
            current_task_title=ws.current_task_title,
            current_project_id=ws.current_project_id,
            current_project_name=ws.current_project_name,
            current_activity_summary=ws.current_activity_summary,
            active_agent_id=ws.active_agent_id,
            active_tool_name=ws.active_tool_name,
            active_model_id=ws.active_model_id,
            is_manager=ws.is_manager,
            updated_at=ws.updated_at,
        )
        if isinstance(self._session, AsyncSession):
            # Async execution path
            pass
        else:
            self._session.merge(model)
            self._session.commit()
        return ws

    def get_workstation(self, employee_id: str) -> Optional[EmployeeWorkstationProjection]:
        if isinstance(self._session, AsyncSession):
            return None
        model = self._session.get(OfficeWorkstationModel, employee_id)
        if not model:
            return None
        return self._model_to_workstation(model)

    def list_workstations(self, department_id: Optional[str] = None) -> List[EmployeeWorkstationProjection]:
        if isinstance(self._session, AsyncSession):
            return []
        stmt = select(OfficeWorkstationModel)
        if department_id:
            stmt = stmt.where(OfficeWorkstationModel.department_id == department_id)
        models = self._session.scalars(stmt).all()
        return [self._model_to_workstation(m) for m in models]

    def record_activity(self, item: OfficeActivityItem) -> OfficeActivityItem:
        model = OfficeActivityModel(
            id=item.activity_id,
            title=item.title,
            description=item.description,
            category=item.category,
            actor_id=item.actor_id,
            entity_id=item.entity_id,
            created_at=item.timestamp,
        )
        if not isinstance(self._session, AsyncSession):
            self._session.merge(model)
            self._session.commit()
        return item

    def get_recent_activities(self, limit: int = 20) -> List[OfficeActivityItem]:
        if isinstance(self._session, AsyncSession):
            return []
        stmt = select(OfficeActivityModel).order_by(desc(OfficeActivityModel.created_at)).limit(limit)
        models = self._session.scalars(stmt).all()
        return [
            OfficeActivityItem(
                activity_id=m.id,
                title=m.title,
                description=m.description,
                category=m.category,
                actor_id=m.actor_id,
                entity_id=m.entity_id,
                timestamp=m.created_at,
            )
            for m in models
        ]

    def list_recent_activity(self, limit: int = 20) -> List[OfficeActivityItem]:
        return self.get_recent_activities(limit)

    def save_attention_item(self, item: HumanAttentionItem) -> HumanAttentionItem:
        model = HumanAttentionModel(
            id=item.item_id,
            attention_type=item.attention_type.value if hasattr(item.attention_type, "value") else str(item.attention_type),
            title=item.title,
            description=item.description,
            entity_id=item.entity_id,
            entity_type=item.entity_type,
            severity=item.severity,
            action_url=item.action_url,
            created_at=item.created_at,
        )
        if not isinstance(self._session, AsyncSession):
            self._session.merge(model)
            self._session.commit()
        return item

    def get_attention_queue(self) -> List[HumanAttentionItem]:
        if isinstance(self._session, AsyncSession):
            return []
        stmt = select(HumanAttentionModel).order_by(desc(HumanAttentionModel.created_at))
        models = self._session.scalars(stmt).all()
        return [
            HumanAttentionItem(
                item_id=m.id,
                attention_type=HumanAttentionType(m.attention_type),
                title=m.title,
                description=m.description,
                entity_id=m.entity_id,
                entity_type=m.entity_type,
                severity=m.severity,
                action_url=m.action_url,
                created_at=m.created_at,
            )
            for m in models
        ]

    def list_human_attention_items(self) -> List[HumanAttentionItem]:
        return self.get_attention_queue()

    def delete_attention_item(self, item_id: str) -> None:
        if not isinstance(self._session, AsyncSession):
            model = self._session.get(HumanAttentionModel, item_id)
            if model:
                self._session.delete(model)
                self._session.commit()

    def _model_to_workstation(self, m: OfficeWorkstationModel) -> EmployeeWorkstationProjection:
        return EmployeeWorkstationProjection(
            employee_id=m.employee_id,
            employee_name=m.employee_name,
            employee_title=m.employee_title,
            role=m.role,
            department_id=m.department_id,
            manager_id=m.manager_id,
            desk_id=m.desk_id,
            area_type=OfficeAreaType(m.area_type),
            visual_state=EmployeeVisualState(m.visual_state),
            current_task_id=m.current_task_id,
            current_task_title=m.current_task_title,
            current_project_id=m.current_project_id,
            current_project_name=m.current_project_name,
            current_activity_summary=m.current_activity_summary,
            active_agent_id=m.active_agent_id,
            active_tool_name=m.active_tool_name,
            active_model_id=m.active_model_id,
            is_manager=m.is_manager,
            updated_at=m.updated_at,
        )
