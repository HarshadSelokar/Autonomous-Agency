"""
Application service for Delegated Governance, Policy Inheritance, Authority Delegation, and Knowledge Sharing Policies.
"""

from datetime import datetime, timezone, UTC
from typing import Any, Dict, List, Optional

from src.domain.enterprise import (
    EnterprisePolicyProfile,
    AuthorityGrant,
    EnterpriseKnowledgeSharingPolicy,
    EnterpriseLearnedPropagation,
    DataClassification,
)
from src.domain.exceptions import (
    AuthorityExpiredError,
    UnauthorizedEnterpriseActionError,
)
from src.domain.repository import EnterpriseRepositoryInterface


class EnterpriseGovernanceService:

    def __init__(self, repository: EnterpriseRepositoryInterface) -> None:
        self.repo = repository

    async def set_policy_profile(
        self,
        enterprise_id: str,
        node_id: str,
        mandatory_security_level: str = "HIGH",
        max_single_budget_spend_usd: float = 50000.0,
        prohibited_external_actions: Optional[List[str]] = None,
        require_human_governance: bool = True,
    ) -> EnterprisePolicyProfile:

        profile = EnterprisePolicyProfile(
            enterprise_id=enterprise_id,
            node_id=node_id,
            mandatory_security_level=mandatory_security_level,
            max_single_budget_spend_usd=max_single_budget_spend_usd,
            prohibited_external_actions=prohibited_external_actions or ["DIRECT_LEGAL_CONTRACT", "UNAPPROVED_PAYMENT"],
            require_human_governance=require_human_governance,
        )
        return await self.repo.save_policy_profile(profile)

    async def resolve_effective_policy(
        self,
        enterprise_id: str,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Deterministically resolves effective policy from root Enterprise down to node.
        Rule: More-specific child policy cannot weaken higher-level mandatory safety/security policies.
        """
        ent_profile = await self.repo.get_policy_profile_by_node_id(enterprise_id)
        node_profile = await self.repo.get_policy_profile_by_node_id(node_id) if node_id != enterprise_id else ent_profile

        # Default fallbacks
        base_security = ent_profile.mandatory_security_level if ent_profile else "HIGH"
        base_max_spend = ent_profile.max_single_budget_spend_usd if ent_profile else 50000.0
        base_prohibited = set(ent_profile.prohibited_external_actions) if ent_profile else {"DIRECT_LEGAL_CONTRACT", "UNAPPROVED_PAYMENT"}

        if node_profile and node_id != enterprise_id:
            # CHILD CANNOT WEAKEN MANDATORY CONSTRAINTS
            node_max_spend = min(node_profile.max_single_budget_spend_usd, base_max_spend)
            combined_prohibited = list(base_prohibited.union(set(node_profile.prohibited_external_actions)))
            req_gov = ent_profile.require_human_governance or node_profile.require_human_governance if ent_profile else node_profile.require_human_governance
        else:
            node_max_spend = base_max_spend
            combined_prohibited = list(base_prohibited)
            req_gov = ent_profile.require_human_governance if ent_profile else True

        return {
            "enterprise_id": enterprise_id,
            "target_node_id": node_id,
            "effective_mandatory_security_level": base_security,
            "effective_max_single_budget_spend_usd": node_max_spend,
            "effective_prohibited_external_actions": combined_prohibited,
            "effective_require_human_governance": req_gov,
        }

    async def grant_authority(
        self,
        enterprise_id: str,
        grantor_node_id: str,
        grantee_node_id: str,
        scope: str,
        action: str,
        max_impact_usd: float = 100000.0,
        expires_at: Optional[datetime] = None,
    ) -> AuthorityGrant:

        grant = AuthorityGrant(
            enterprise_id=enterprise_id,
            grantor_node_id=grantor_node_id,
            grantee_node_id=grantee_node_id,
            scope=scope,
            action=action,
            max_impact_usd=max_impact_usd,
            expires_at=expires_at,
            is_revoked=False,
        )
        return await self.repo.save_authority_grant(grant)

    async def verify_authority(
        self,
        enterprise_id: str,
        grantee_node_id: str,
        action: str,
        impact_usd: float = 0.0,
    ) -> bool:

        grants = await self.repo.list_authority_grants_for_enterprise(enterprise_id)
        valid_grant = None

        now = datetime.now(UTC)
        for g in grants:
            if g.grantee_node_id == grantee_node_id and g.action == action and not g.is_revoked:
                if g.expires_at and g.expires_at < now:
                    continue
                if g.max_impact_usd >= impact_usd:
                    valid_grant = g
                    break

        if not valid_grant:
            raise AuthorityExpiredError(
                f"grant-{grantee_node_id}-{action}",
                reason=f"No valid non-expired authority grant found for action '{action}' with impact ${impact_usd:,.2f} on node '{grantee_node_id}'."
            )
        return True

    async def create_knowledge_sharing_policy(
        self,
        enterprise_id: str,
        source_company_id: str,
        target_company_id: str,
        allowed_classifications: Optional[List[DataClassification]] = None,
    ) -> EnterpriseKnowledgeSharingPolicy:

        policy = EnterpriseKnowledgeSharingPolicy(
            enterprise_id=enterprise_id,
            source_company_id=source_company_id,
            target_company_id=target_company_id,
            allowed_classifications=allowed_classifications or [DataClassification.PUBLIC, DataClassification.INTERNAL],
            governance_approved=True,
        )
        return policy

    async def propagate_learned_lesson(
        self,
        enterprise_id: str,
        source_company_id: str,
        learning_candidate_id: str,
        lesson_summary: str,
        applicability_conditions: str,
        governance_approval_id: str,
    ) -> EnterpriseLearnedPropagation:

        prop = EnterpriseLearnedPropagation(
            enterprise_id=enterprise_id,
            source_company_id=source_company_id,
            learning_candidate_id=learning_candidate_id,
            lesson_summary=lesson_summary,
            applicability_conditions=applicability_conditions,
            governance_approval_id=governance_approval_id,
        )
        return prop
