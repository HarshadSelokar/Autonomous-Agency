"""
Application service for managing Enterprise Organizational Topology Graph and Cycle Validation.
"""

from typing import Any, Dict, List, Optional

from src.domain.enterprise import (
    EnterpriseOrganizationNode,
    EnterpriseRelationship,
    NodeType,
    RelationshipType,
    DataClassification,
)
from src.domain.exceptions import InvalidTopologyCycleError
from src.domain.repository import EnterpriseRepositoryInterface


class EnterpriseTopologyService:

    def __init__(self, repository: EnterpriseRepositoryInterface) -> None:
        self.repo = repository

    async def create_node(
        self,
        enterprise_id: str,
        name: str,
        node_type: NodeType,
        reference_id: Optional[str] = None,
        parent_node_id: Optional[str] = None,
        region: str = "GLOBAL",
        data_classification: DataClassification = DataClassification.INTERNAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EnterpriseOrganizationNode:

        if parent_node_id:
            await self._validate_no_cycle(enterprise_id, child_id="new_node", parent_id=parent_node_id)

        node = EnterpriseOrganizationNode(
            enterprise_id=enterprise_id,
            name=name,
            node_type=node_type,
            reference_id=reference_id,
            parent_node_id=parent_node_id,
            region=region,
            data_classification=data_classification,
            metadata=metadata or {},
        )
        return await self.repo.save_topology_node(node)

    async def add_relationship(
        self,
        enterprise_id: str,
        source_node_id: str,
        target_node_id: str,
        relationship_type: RelationshipType = RelationshipType.PARENT_CHILD,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EnterpriseRelationship:

        if relationship_type == RelationshipType.PARENT_CHILD:
            await self._validate_no_cycle(enterprise_id, child_id=target_node_id, parent_id=source_node_id)

        rel = EnterpriseRelationship(
            enterprise_id=enterprise_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship_type=relationship_type,
            description=description,
            metadata=metadata or {},
        )
        return await self.repo.save_relationship(rel)

    async def _validate_no_cycle(self, enterprise_id: str, child_id: str, parent_id: str) -> None:
        if child_id == parent_id:
            raise InvalidTopologyCycleError(enterprise_id, child_id, parent_id)

        nodes = await self.repo.list_topology_nodes_for_enterprise(enterprise_id)
        parent_map = {n.id: n.parent_node_id for n in nodes}

        curr = parent_id
        visited = set()

        while curr:
            if curr == child_id:
                raise InvalidTopologyCycleError(enterprise_id, child_id, parent_id)
            if curr in visited:
                break
            visited.add(curr)
            curr = parent_map.get(curr)

    async def get_topology_tree(self, enterprise_id: str) -> Dict[str, Any]:
        nodes = await self.repo.list_topology_nodes_for_enterprise(enterprise_id)
        rels = await self.repo.list_relationships_for_enterprise(enterprise_id)

        root_nodes = [n for n in nodes if not n.parent_node_id]

        def build_node_tree(node: EnterpriseOrganizationNode) -> Dict[str, Any]:
            children = [n for n in nodes if n.parent_node_id == node.id]
            return {
                "id": node.id,
                "name": node.name,
                "node_type": node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type),
                "reference_id": node.reference_id,
                "region": node.region,
                "data_classification": node.data_classification.value if hasattr(node.data_classification, "value") else str(node.data_classification),
                "children": [build_node_tree(c) for c in children],
            }

        return {
            "enterprise_id": enterprise_id,
            "total_nodes_count": len(nodes),
            "total_relationships_count": len(rels),
            "tree": [build_node_tree(r) for r in root_nodes],
        }
