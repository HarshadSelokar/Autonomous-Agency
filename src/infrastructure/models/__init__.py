"""
Infrastructure ORM models package.
Import all ORM models to ensure registration with Base.metadata.
"""

from src.infrastructure.models.agent_model import AgentModel
from src.infrastructure.models.artifact_model import ArtifactModel
from src.infrastructure.models.assignment_model import AssignmentModel
from src.infrastructure.models.checkpoint_model import AgentCheckpointModel
from src.infrastructure.models.conversation_model import ConversationModel
from src.infrastructure.models.decision_model import (
    DecisionAuditModel,
    DecisionModel,
    ManagerDecisionModel,
)
from src.infrastructure.models.department_model import DepartmentModel
from src.infrastructure.models.employee_model import EmployeeModel
from src.infrastructure.models.meeting_model import (
    MeetingAgendaItemModel,
    MeetingAttendanceModel,
    MeetingModel,
    MeetingParticipantModel,
)
from src.infrastructure.models.memory_model import MemoryModel
from src.infrastructure.models.message_model import MessageModel
from src.infrastructure.models.objective_model import ObjectiveModel
from src.infrastructure.models.outbox_model import OutboxMessageModel
from src.infrastructure.models.plan_model import PlanModel
from src.infrastructure.models.run_model import AgentRunModel
from src.infrastructure.models.software_company_model import (
    CodeChangeModel,
    CodeReviewModel,
    EngineeringPlanModel,
    SoftwareDefectModel,
    SoftwareDeliveryModel,
    SoftwareProjectModel,
    SoftwareRequirementModel,
    TestRunModel,
)
from src.infrastructure.models.step_model import ExecutionStepModel
from src.infrastructure.models.task_dependency_model import TaskDependencyModel
from src.infrastructure.models.task_model import TaskModel
from src.infrastructure.models.verification_model import (
    ExpectedOutcomeModel,
    FailureRecordModel,
    RecoveryActionModel,
    VerificationEvidenceModel,
    VerificationModel,
)
from src.infrastructure.models.governance_model import (
    EmergencyStopModel,
    GovernanceApprovalRequestModel,
    GovernanceOverrideModel,
    GovernancePolicyModel,
    HumanInterventionModel,
    PolicyViolationModel,
)
from src.infrastructure.models.model_routing_model import (
    ModelProfileModel,
    ModelProviderHealthModel,
    ModelSelectionDecisionModel,
)
from src.infrastructure.models.office_model import (
    HumanAttentionModel,
    OfficeActivityModel,
    OfficeWorkstationModel,
)
from src.infrastructure.models.cross_department_model import (
    DepartmentHandoffModel,
    DepartmentRequestModel,
    DepartmentServiceContractModel,
)
from src.infrastructure.models.workforce_model import (
    CapabilityGapModel,
    CapacitySnapshotModel,
    EmployeeTemplateModel,
    StaffingRecommendationModel,
    WorkforceAllocationModel,
    WorkforceChangeRequestModel,
    WorkforceDecisionModel,
    WorkforceDemandModel,
    WorkforcePlanModel,
)
from src.infrastructure.models.team_model import (
    TeamMemberModel,
    TeamModel,
)
from src.infrastructure.models.work_item_model import WorkItemModel
from src.infrastructure.models.workspace_model import WorkspaceModel

from src.infrastructure.models.company_model import (
    AutonomousCompanyModel,
    CompanyHealthSnapshotModel,
    CompanyMetricSnapshotModel,
    CompanyOperatingCycleModel,
    CompanyOpportunityModel,
    CompanyRiskModel,
    CompanyStrategyModel,
    ContinuousImprovementProposalModel,
    PortfolioItemModel,
)
from src.infrastructure.models.business_model import (
    BusinessAccountModel,
    BusinessTransactionModel,
    RevenueRecordModel,
    ExpenseRecordModel,
    InvoiceModel,
    InvoiceLineModel,
    PaymentModel,
    SubscriptionModel,
    OrderModel,
    CustomerAccountModel,
    VendorModel,
    ProcurementRequestModel,
    PurchaseOrderModel,
    BudgetModel,
    BudgetAllocationModel,
    FinancialPeriodModel,
    ReconciliationModel,
    ReconciliationItemModel,
    CashFlowSnapshotModel,
    BusinessMetricModel,
    BusinessProcessModel,
)
from src.infrastructure.models.gtm_model import (
    ProductModel,
    ProductVersionModel,
    ProductRoadmapModel,
    ProductRequirementModel,
    ProductFeedbackModel,
    CustomerModel,
    CustomerContactModel,
    CustomerInteractionModel,
    CustomerHealthSnapshotModel,
    CustomerOutcomeModel,
    LeadModel,
    OpportunityModel,
    SalesActivityModel,
    ProposalModel,
    CustomerOnboardingPlanModel,
    SupportCaseModel,
    MarketingCampaignModel,
    MarketingAssetModel,
    CommunicationPreferenceModel,
    GTMMetricModel,
)
from src.infrastructure.models.company_model import (
    ResourceAllocationPlanModel,
    StrategicAnalysisModel,
    StrategicInitiativeModel,
    StrategicObjectiveModel,
    StrategyProposalModel,
    StrategySimulationModel,
)

__all__ = [
    "AgentModel",
    "ArtifactModel",
    "AssignmentModel",
    "AgentCheckpointModel",
    "ConversationModel",
    "DecisionModel",
    "DecisionAuditModel",
    "ManagerDecisionModel",
    "DepartmentModel",
    "EmployeeModel",
    "MeetingModel",
    "MeetingParticipantModel",
    "MeetingAttendanceModel",
    "MeetingAgendaItemModel",
    "MemoryModel",
    "MessageModel",
    "ObjectiveModel",
    "OutboxMessageModel",
    "PlanModel",
    "AgentRunModel",
    "ExecutionStepModel",
    "TaskDependencyModel",
    "TaskModel",
    "WorkItemModel",
    "WorkspaceModel",
    "SoftwareProjectModel",
    "SoftwareRequirementModel",
    "EngineeringPlanModel",
    "CodeChangeModel",
    "CodeReviewModel",
    "TestRunModel",
    "SoftwareDefectModel",
    "SoftwareDeliveryModel",
    "VerificationModel",
    "ExpectedOutcomeModel",
    "VerificationEvidenceModel",
    "FailureRecordModel",
    "RecoveryActionModel",
    "GovernancePolicyModel",
    "GovernanceApprovalRequestModel",
    "HumanInterventionModel",
    "EmergencyStopModel",
    "GovernanceOverrideModel",
    "PolicyViolationModel",
    "ModelProfileModel",
    "ModelSelectionDecisionModel",
    "ModelProviderHealthModel",
    "OfficeWorkstationModel",
    "OfficeActivityModel",
    "HumanAttentionModel",
    "DepartmentRequestModel",
    "DepartmentHandoffModel",
    "DepartmentServiceContractModel",
    "WorkforceDemandModel",
    "CapacitySnapshotModel",
    "CapabilityGapModel",
    "StaffingRecommendationModel",
    "WorkforceAllocationModel",
    "WorkforceChangeRequestModel",
    "WorkforceDecisionModel",
    "EmployeeTemplateModel",
    "WorkforcePlanModel",
    "TeamModel",
    "TeamMemberModel",
    "AutonomousCompanyModel",
    "CompanyOperatingCycleModel",
    "CompanyStrategyModel",
    "StrategicObjectiveModel",
    "StrategicInitiativeModel",
    "CompanyMetricSnapshotModel",
    "CompanyHealthSnapshotModel",
    "CompanyRiskModel",
    "CompanyOpportunityModel",
    "StrategicAnalysisModel",
    "StrategyProposalModel",
    "PortfolioItemModel",
    "ResourceAllocationPlanModel",
    "ContinuousImprovementProposalModel",
    "StrategySimulationModel",
    "KnowledgeItemModel",
    "KnowledgeClaimModel",
    "KnowledgeProvenanceModel",
    "KnowledgeValidationModel",
    "KnowledgeConflictModel",
    "KnowledgeRelationshipModel",
    "KnowledgeProcedureModel",
    "OrganizationalExperimentModel",
    "KnowledgeUsageRecordModel",
]

from src.infrastructure.models.knowledge_model import (
    KnowledgeClaimModel,
    KnowledgeConflictModel,
    KnowledgeItemModel,
    KnowledgeProcedureModel,
    KnowledgeProvenanceModel,
    KnowledgeRelationshipModel,
    KnowledgeUsageRecordModel,
    KnowledgeValidationModel,
    OrganizationalExperimentModel,
)
from src.infrastructure.models.research_model import (
    InnovationProposalModel,
    ResearchBenchmarkModel,
    ResearchDiscoveryModel,
    ResearchEvidenceModel,
    ResearchFindingModel,
    ResearchHypothesisModel,
    ResearchOpportunityModel,
    ResearchPlanModel,
    ResearchProgramModel,
    ResearchQuestionModel,
    ResearchRequestModel,
    ResearchSourceModel,
    TechnologyEvaluationModel,
)

__all__.extend(
    [
        "ResearchProgramModel",
        "ResearchRequestModel",
        "ResearchQuestionModel",
        "ResearchPlanModel",
        "ResearchSourceModel",
        "ResearchEvidenceModel",
        "ResearchFindingModel",
        "ResearchHypothesisModel",
        "ResearchBenchmarkModel",
        "TechnologyEvaluationModel",
        "ResearchDiscoveryModel",
        "ResearchOpportunityModel",
        "InnovationProposalModel",
    ]
)

from src.infrastructure.models.company_model import (
    CompanyModel,
    CompanyProfileModel,
    CompanyMembershipModel,
    CompanyTemplateModel,
    CompanyRelationshipModel,
    CompanyDataShareRequestModel,
    CompanyResourceQuotaModel,
    CompanyResourceUsageModel,
    CompanySimulationModel,
    SimulationSnapshotModel,
    SimulationScenarioModel,
    SimulationResultModel,
    SimulationFinancialRecordModel,
)

__all__.extend(
    [
        "CompanyModel",
        "CompanyProfileModel",
        "CompanyMembershipModel",
        "CompanyTemplateModel",
        "CompanyRelationshipModel",
        "CompanyDataShareRequestModel",
        "CompanyResourceQuotaModel",
        "CompanyResourceUsageModel",
        "CompanySimulationModel",
        "SimulationSnapshotModel",
        "SimulationScenarioModel",
        "SimulationResultModel",
        "SimulationFinancialRecordModel",
    ]
)




