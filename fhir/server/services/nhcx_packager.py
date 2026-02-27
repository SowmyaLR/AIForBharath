"""
NHCX Bundle Packager.

Assembles all FHIR resources (Patient, Composition, DiagnosticReport, etc.)
into a single ABDM FHIR R4 Bundle conforming to NHCX Claim profiles.

The output Bundle includes:
  - A FHIR Claim resource linking all supporting documents
  - One resource per uploaded document (Composition / DiagnosticReport / etc.)
  - Patient and Coverage resources
  - All embedded Observations from DiagnosticReports
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "profiles.yaml")


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_uuid() -> str:
    return str(uuid.uuid4())


def build_claim_resource(
    patient_id_ref: str,
    coverage_id_ref: str,
    supporting_resources: List[dict],
    insurer_name: Optional[str],
    config: dict,
) -> dict:
    """
    Build the NHCX FHIR Claim resource.
    supporting_resources: list of FHIR resource dicts that are the claim evidence.
    """
    nhcx = config["nhcx"]
    now = _now_iso()

    supporting_info = []
    for i, res in enumerate(supporting_resources):
        res_type = res.get("resourceType", "Unknown")
        res_id = res.get("id", _new_uuid())
        supporting_info.append({
            "sequence": i + 1,
            "category": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/claiminformationcategory",
                    "code": "info",
                    "display": "Information",
                }]
            },
            "valueReference": {"reference": f"{res_type}/{res_id}"},
        })

    claim = {
        "resourceType": "Claim",
        "id": _new_uuid(),
        "meta": {
            "profile": [nhcx["profile_url"]]
        },
        "status": "active",
        "type": {
            "coding": [nhcx["claim_type"]]
        },
        "subType": {
            "coding": [nhcx["claim_subtype"]]
        },
        "use": nhcx["use_code"]["code"],
        "patient": {"reference": f"Patient/{patient_id_ref}"},
        "created": now,
        "insurer": {"display": insurer_name or "Unknown Insurer"},
        "provider": {"display": "Healthcare Provider"},
        "insurance": [
            {
                "sequence": 1,
                "focal": True,
                "coverage": {"reference": f"Coverage/{coverage_id_ref}"},
            }
        ],
        "supportingInfo": supporting_info,
        "total": {
            "value": 0.0,
            "currency": "INR",
        },
    }
    return claim


def package_nhcx_bundle(
    patient_resource: dict,
    coverage_resource: dict,
    document_resources: List[Tuple[str, dict]],  # [(filename, resource_dict)]
    insurer_name: Optional[str] = None,
    config: Optional[dict] = None,
) -> dict:
    """
    Assemble the final NHCX-conformant FHIR Bundle.

    Args:
        patient_resource: FHIR Patient dict
        coverage_resource: FHIR Coverage dict
        document_resources: list of (filename, fhir_resource) per uploaded document
        insurer_name: optional insurer display name
        config: loaded profiles.yaml config

    Returns:
        Complete FHIR Bundle dict
    """
    if config is None:
        config = _load_config()

    patient_id = patient_resource["id"]
    coverage_id = coverage_resource["id"]

    # Collect all primary resources and embedded observations
    primary_resources = []
    all_observations = []

    for _filename, resource in document_resources:
        # Pull out embedded observations (added by fhir_builder for DiagnosticReports)
        embedded_obs = resource.pop("_embedded_observations", [])
        all_observations.extend(embedded_obs)

        # Pull out embedded all_medications for prescriptions
        all_meds = resource.pop("_all_medications", None)
        primary_resources.append(resource)
        if all_meds and len(all_meds) > 1:
            # Add remaining medications (first was used as primary)
            primary_resources.extend(all_meds[1:])

    # Build the Claim resource referencing all primary clinical resources
    claim = build_claim_resource(
        patient_id_ref=patient_id,
        coverage_id_ref=coverage_id,
        supporting_resources=primary_resources,
        insurer_name=insurer_name,
        config=config,
    )

    # Assemble entries
    entries = []

    def _entry(resource: dict) -> dict:
        rid = resource.get("id", _new_uuid())
        rtype = resource.get("resourceType", "Resource")
        return {
            "fullUrl": f"urn:uuid:{rid}",
            "resource": resource,
        }

    # Order: Claim first, then Patient, Coverage, clinical resources, observations
    entries.append(_entry(claim))
    entries.append(_entry(patient_resource))
    entries.append(_entry(coverage_resource))
    for res in primary_resources:
        entries.append(_entry(res))
    for obs in all_observations:
        entries.append(_entry(obs))

    bundle = {
        "resourceType": "Bundle",
        "id": _new_uuid(),
        "meta": {
            "profile": [config["nhcx"]["profile_url"]],
            "lastUpdated": _now_iso(),
        },
        "identifier": {
            "system": "https://nrces.in/ndhm/fhir/r4/NamingSystem/ndhm-bundleID",
            "value": _new_uuid(),
        },
        "type": "collection",
        "timestamp": _now_iso(),
        "entry": entries,
    }

    return bundle
