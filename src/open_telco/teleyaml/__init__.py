"""Teleyaml_v2: YAML configuration evaluation for 5G network functions.

This module evaluates LLM capabilities for generating valid YAML configurations
for 5G core network functions (AMF, Slice Deployment, UE Provisioning).
"""

from open_telco.teleyaml.tasks.amf_configuration import amf_configuration
from open_telco.teleyaml.tasks.slice_deployment import slice_deployment
from open_telco.teleyaml.tasks.ue_provisioning import ue_provisioning

__all__ = ["amf_configuration", "slice_deployment", "ue_provisioning"]
