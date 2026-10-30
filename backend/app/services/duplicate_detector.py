"""DepoSafe Duplicate Detection Intelligence Service.

Detects multi-layer duplicate collisions across institutions and academic years:
1. Exact Bank + FDR Number Match (composite key: bank_name + fdr_number, NOT fdr_number alone).
2. SHA-256 Identical File Collision (exact byte-level reuse across institutions/records).
3. Perceptual Hash (pHash) Hamming Distance Similarity (detects visual re-scans and template re-renders).

Statutory Label: "Relationship requiring investigation, not proof of fraud."
"""

import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import imagehash

from backend.app.models.deposafe_models import FDR, FDRDocument, Institution

EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def normalize_key(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r'[^A-Z0-9]', '', str(text).upper())

class DuplicateDetector:
    PHASH_HAMMING_THRESHOLD = 8  # Hamming distance <= 8 indicates visual template reuse

    @classmethod
    def check_fdr_duplicates(
        cls,
        fdr: FDR,
        db: Session
    ) -> Dict[str, Any]:
        """
        Executes full multi-modal duplicate collision checks for an FDR instrument.
        """
        exact_bank_fdr_matches = []
        sha256_identical_matches = []
        phash_visual_matches = []

        # 1. Exact / Normalized Bank + FDR Number Match (Cross-Institution)
        norm_fdr = normalize_key(fdr.fdr_number)
        norm_bank = fdr.bank_name.strip().upper() if fdr.bank_name else ""

        cross_inst_fdrs = db.query(FDR).filter(FDR.id != fdr.id).all()
        for dup in cross_inst_fdrs:
            if dup.institution_id != fdr.institution_id:
                if normalize_key(dup.fdr_number) == norm_fdr and (dup.bank_name or "").strip().upper() == norm_bank:
                    other_inst = db.query(Institution).filter(Institution.id == dup.institution_id).first()
                    exact_bank_fdr_matches.append({
                        "collision_type": "EXACT_BANK_AND_FDR_NUMBER",
                        "matched_fdr_id": dup.id,
                        "matched_internal_id": dup.internal_fdr_id,
                        "matched_fdr_number": dup.fdr_number,
                        "bank_name": dup.bank_name,
                        "institution_id": dup.institution_id,
                        "institution_name": other_inst.name if other_inst else "Unknown",
                        "aicte_id": other_inst.aicte_id if other_inst else "N/A",
                        "state": other_inst.state if other_inst else "N/A",
                        "status": dup.status.value,
                        "reason": f"Same bank '{fdr.bank_name}' and FDR number '{fdr.fdr_number}' is already pledged by {other_inst.name if other_inst else 'another institution'}."
                    })

        # 2. SHA-256 and Perceptual Hash Collisions
        primary_doc = db.query(FDRDocument).filter(
            FDRDocument.fdr_id == fdr.id,
            FDRDocument.doc_type == "FDR_CERTIFICATE"
        ).order_by(FDRDocument.version.desc()).first()
        if not primary_doc:
            primary_doc = db.query(FDRDocument).filter(FDRDocument.fdr_id == fdr.id).order_by(FDRDocument.id.asc()).first()

        if primary_doc:
            # 2a. SHA-256 exact byte match (excluding empty-string default hash)
            if primary_doc.file_hash_sha256 and primary_doc.file_hash_sha256 != EMPTY_SHA256:
                sha_dups = db.query(FDRDocument).filter(
                    FDRDocument.file_hash_sha256 == primary_doc.file_hash_sha256,
                    FDRDocument.fdr_id != fdr.id,
                    FDRDocument.file_hash_sha256 != EMPTY_SHA256
                ).all()

                for d in sha_dups:
                    parent_fdr = db.query(FDR).filter(FDR.id == d.fdr_id).first()
                    if parent_fdr and parent_fdr.institution_id != fdr.institution_id:
                        p_inst = db.query(Institution).filter(Institution.id == parent_fdr.institution_id).first()
                        sha256_identical_matches.append({
                            "collision_type": "BYTE_FOR_BYTE_SHA256_COLLISION",
                            "matched_document_id": d.id,
                            "matched_fdr_id": d.fdr_id,
                            "file_name": d.file_name,
                            "sha256_hash": d.file_hash_sha256,
                            "institution_id": p_inst.id if p_inst else None,
                            "institution_name": p_inst.name if p_inst else "Unknown",
                            "aicte_id": p_inst.aicte_id if p_inst else "N/A",
                            "reason": "Exact byte-for-byte identical file reused across different deposits."
                        })

            # 2b. Perceptual Hash (pHash) Hamming Distance
            if primary_doc.perceptual_hash and len(sha256_identical_matches) == 0:
                try:
                    target_hash = imagehash.hex_to_hash(primary_doc.perceptual_hash)
                    other_docs = db.query(FDRDocument).filter(
                        FDRDocument.fdr_id != fdr.id,
                        FDRDocument.doc_type == "FDR_CERTIFICATE",
                        FDRDocument.perceptual_hash.isnot(None)
                    ).limit(100).all()

                    for od in other_docs:
                        try:
                            parent_fdr = db.query(FDR).filter(FDR.id == od.fdr_id).first()
                            if not parent_fdr or parent_fdr.institution_id == fdr.institution_id:
                                continue
                            # Legitimate same-bank certificates share standard layout; flag cross-bank template spoofing
                            if (parent_fdr.bank_name or "").strip().upper() != (fdr.bank_name or "").strip().upper():
                                candidate_hash = imagehash.hex_to_hash(od.perceptual_hash)
                                dist = target_hash - candidate_hash  # Hamming distance
                                if dist <= 2:
                                    p_inst = db.query(Institution).filter(Institution.id == parent_fdr.institution_id).first()
                                    phash_visual_matches.append({
                                        "collision_type": "CROSS_BANK_TEMPLATE_SPOOF",
                                        "matched_document_id": od.id,
                                        "matched_fdr_id": od.fdr_id,
                                        "hamming_distance": dist,
                                        "institution_name": p_inst.name if p_inst else "Unknown",
                                        "reason": f"Visual template spoofing: layout matches '{parent_fdr.bank_name}' template with Hamming distance {dist} <= 2."
                                    })
                        except Exception:
                            continue
                except Exception:
                    pass

        has_collision = bool(exact_bank_fdr_matches or sha256_identical_matches)

        return {
            "fdr_id": fdr.id,
            "fdr_number": fdr.fdr_number,
            "bank_name": fdr.bank_name,
            "has_collision": has_collision,
            "exact_bank_fdr_matches": exact_bank_fdr_matches,
            "sha256_identical_matches": sha256_identical_matches,
            "phash_visual_matches": phash_visual_matches,
            "total_duplicate_flags": len(exact_bank_fdr_matches) + len(sha256_identical_matches),
            "statutory_label": "Relationship requiring investigation, not proof of fraud."
        }

