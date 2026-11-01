"""
Request-scoped tenant context and automatic tenant scoping for the ORM.

Every table carries a tenant_id column (declared once on the declarative Base). While a
tenant is bound to the current context:

- every ORM SELECT / UPDATE / DELETE is restricted to that tenant's rows, and
- new rows are stamped with that tenant.

With no tenant bound (platform admin without X-Tenant-ID, background workers, tests with
authentication off) nothing is filtered or stamped.
"""

from contextvars import ContextVar

from sqlalchemy import event
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria

_current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)
_current_tenant_slug: ContextVar[str | None] = ContextVar("current_tenant_slug", default=None)


def get_current_tenant_id() -> str | None:
    return _current_tenant_id.get()


def get_current_tenant_slug() -> str | None:
    return _current_tenant_slug.get()


def set_current_tenant_id(tenant_id: str | None) -> None:
    _current_tenant_id.set(tenant_id)


def set_current_tenant_slug(tenant_slug: str | None) -> None:
    _current_tenant_slug.set(tenant_slug)


def install_tenant_scoping(base: type) -> None:
    """Register the session listeners that enforce tenant scoping for models of `base`."""

    @event.listens_for(Session, "do_orm_execute")
    def _scope_statements(state: ORMExecuteState) -> None:
        tenant_id = _current_tenant_id.get()
        if tenant_id is None or state.execution_options.get("skip_tenant_scope", False):
            return
        if not (state.is_select or state.is_update or state.is_delete):
            return
        if state.is_column_load or state.is_relationship_load:
            return
        state.statement = state.statement.options(
            with_loader_criteria(
                base,
                lambda cls: cls.tenant_id == tenant_id,
                include_aliases=True,
            )
        )

    @event.listens_for(Session, "before_flush")
    def _stamp_new_rows(session: Session, flush_context: object, instances: object) -> None:
        tenant_id = _current_tenant_id.get()
        for obj in session.new:
            if not isinstance(obj, base):
                continue
            if getattr(obj, "__tenant_is_self__", False):
                # A tenant row belongs to itself, so its own users can read it
                if getattr(obj, "tenant_id", None) is None:
                    setattr(obj, "tenant_id", getattr(obj, "id", None))
            elif tenant_id is not None and getattr(obj, "tenant_id", None) is None:
                setattr(obj, "tenant_id", tenant_id)
