"""
Operators module for Difference Machine addon
"""
from .export_operator import DFM_SaveGeometryOperator
from .import_operator import DFM_LoadGeometryOperator
from .version_operators import (
    DFM_LoadVersionOperator,
    DFM_ReplaceObjectOperator,
    DFM_CompareVersionsOperator,
    DFM_DeleteVersionOperator
)
from .branch_operators import (
    DFM_CreateBranchOperator,
    DFM_SwitchBranchOperator,
    DFM_ListBranchesOperator,
    DFM_DeleteBranchOperator,
    DFM_GoToBranchOperator
)
from .ui_operators import (
    DFM_ToggleImportAll_OT_operator,
    DFM_ToggleImportNone_OT_operator
)

# Classes list for registration
classes = [
    DFM_SaveGeometryOperator,
    DFM_LoadGeometryOperator,
    DFM_LoadVersionOperator,
    DFM_ReplaceObjectOperator,
    DFM_CompareVersionsOperator,
    DFM_DeleteVersionOperator,
    DFM_CreateBranchOperator,
    DFM_SwitchBranchOperator,
    DFM_ListBranchesOperator,
    DFM_DeleteBranchOperator,
    DFM_GoToBranchOperator,
    DFM_ToggleImportAll_OT_operator,
    DFM_ToggleImportNone_OT_operator
]

__all__ = [
    'DFM_SaveGeometryOperator',
    'DFM_LoadGeometryOperator',
    'DFM_LoadVersionOperator',
    'DFM_ReplaceObjectOperator',
    'DFM_CompareVersionsOperator',
    'DFM_DeleteVersionOperator',
    'DFM_CreateBranchOperator',
    'DFM_SwitchBranchOperator',
    'DFM_ListBranchesOperator',
    'DFM_DeleteBranchOperator',
    'DFM_GoToBranchOperator',
    'DFM_ToggleImportAll_OT_operator',
    'DFM_ToggleImportNone_OT_operator',
    'classes'
]

