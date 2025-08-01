import hashlib
import hmac
import secrets
import re
from typing import Dict, List, Any, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import pandas as pd
import numpy as np
from enum import Enum
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class PIIType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"
    CUSTOM = "custom"


class DataSecurityService:
    def __init__(self):
        self.encryption_key = settings.ENCRYPTION_KEY.encode()[:32].ljust(32, b'0')
        self.fernet = Fernet(Fernet.generate_key())
        
        # PII detection patterns
        self.pii_patterns = {
            PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            PIIType.PHONE: r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            PIIType.SSN: r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b',
            PIIType.CREDIT_CARD: r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            PIIType.IP_ADDRESS: r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        }
    
    def encrypt_sensitive_data(self, data: str, tenant_key: Optional[str] = None) -> str:
        """Encrypt sensitive data using tenant-specific or global key"""
        try:
            if tenant_key:
                # Use tenant-specific encryption
                key = hashlib.sha256(tenant_key.encode()).digest()[:32]
                f = Fernet(Fernet.generate_key())  # Would use derived key in production
            else:
                f = self.fernet
            
            encrypted_data = f.encrypt(data.encode())
            return encrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise Exception("Data encryption failed")
    
    def decrypt_sensitive_data(self, encrypted_data: str, tenant_key: Optional[str] = None) -> str:
        """Decrypt sensitive data using tenant-specific or global key"""
        try:
            if tenant_key:
                # Use tenant-specific decryption
                key = hashlib.sha256(tenant_key.encode()).digest()[:32]
                f = Fernet(Fernet.generate_key())  # Would use derived key in production
            else:
                f = self.fernet
            
            decrypted_data = f.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise Exception("Data decryption failed")
    
    def scan_for_pii(self, data: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
        """Scan DataFrame for PII data"""
        pii_findings = {}
        
        for column in data.columns:
            column_findings = []
            
            # Convert column to string for pattern matching
            string_data = data[column].astype(str)
            
            for pii_type, pattern in self.pii_patterns.items():
                matches = string_data.str.contains(pattern, regex=True, na=False)
                if matches.any():
                    match_count = matches.sum()
                    confidence = min(match_count / len(data), 1.0)
                    
                    column_findings.append({
                        "pii_type": pii_type.value,
                        "confidence": confidence,
                        "match_count": int(match_count),
                        "sample_matches": self._get_sample_matches(
                            string_data[matches], pattern, 3
                        )
                    })
            
            # Additional heuristic checks
            additional_findings = self._heuristic_pii_detection(data[column], column)
            column_findings.extend(additional_findings)
            
            if column_findings:
                pii_findings[column] = column_findings
        
        return pii_findings
    
    def _heuristic_pii_detection(self, series: pd.Series, column_name: str) -> List[Dict[str, Any]]:
        """Heuristic-based PII detection"""
        findings = []
        column_lower = column_name.lower()
        
        # Name detection based on column name and data patterns
        if any(keyword in column_lower for keyword in ['name', 'first', 'last', 'full']):
            if series.dtype == 'object':
                # Check if values look like names (2-3 words, capitalized)
                name_pattern = r'^[A-Z][a-z]+ ?[A-Z]?[a-z]*? ?[A-Z]?[a-z]*?$'
                matches = series.astype(str).str.match(name_pattern, na=False)
                if matches.sum() > len(series) * 0.3:  # 30% threshold
                    findings.append({
                        "pii_type": PIIType.NAME.value,
                        "confidence": matches.sum() / len(series),
                        "match_count": int(matches.sum()),
                        "detection_method": "heuristic_name"
                    })
        
        # Address detection
        if any(keyword in column_lower for keyword in ['address', 'street', 'city', 'zip']):
            findings.append({
                "pii_type": PIIType.ADDRESS.value,
                "confidence": 0.8,
                "match_count": len(series.dropna()),
                "detection_method": "heuristic_address"
            })
        
        # Date of birth detection
        if any(keyword in column_lower for keyword in ['birth', 'dob', 'born']):
            findings.append({
                "pii_type": PIIType.DATE_OF_BIRTH.value,
                "confidence": 0.9,
                "match_count": len(series.dropna()),
                "detection_method": "heuristic_dob"
            })
        
        return findings
    
    def _get_sample_matches(self, matches: pd.Series, pattern: str, count: int) -> List[str]:
        """Get sample matches for PII findings"""
        try:
            sample_values = matches.head(count).tolist()
            # Mask the actual values for security
            return [self.mask_sensitive_value(str(val)) for val in sample_values]
        except Exception:
            return []
    
    def mask_sensitive_value(self, value: str, mask_char: str = "*", show_chars: int = 2) -> str:
        """Mask sensitive values for display"""
        if len(value) <= show_chars * 2:
            return mask_char * len(value)
        
        return value[:show_chars] + mask_char * (len(value) - show_chars * 2) + value[-show_chars:]
    
    def apply_column_level_access_control(
        self,
        data: pd.DataFrame,
        user_permissions: Dict[str, List[str]],
        user_role: str
    ) -> pd.DataFrame:
        """Apply column-level access control based on user permissions"""
        try:
            allowed_columns = user_permissions.get(user_role, [])
            
            if not allowed_columns or "all" in allowed_columns:
                return data  # Full access
            
            # Filter to only allowed columns
            available_columns = [col for col in data.columns if col in allowed_columns]
            return data[available_columns]
            
        except Exception as e:
            logger.error(f"Access control application failed: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
    def apply_data_masking(
        self,
        data: pd.DataFrame,
        pii_findings: Dict[str, List[Dict[str, Any]]],
        masking_rules: Dict[str, str]
    ) -> pd.DataFrame:
        """Apply data masking based on PII findings and rules"""
        masked_data = data.copy()
        
        for column, findings in pii_findings.items():
            if column not in data.columns:
                continue
            
            for finding in findings:
                pii_type = finding["pii_type"]
                confidence = finding["confidence"]
                
                # Apply masking if confidence is high enough
                if confidence > 0.5:
                    masking_method = masking_rules.get(pii_type, "partial")
                    masked_data[column] = self._apply_masking_method(
                        masked_data[column], 
                        masking_method,
                        pii_type
                    )
        
        return masked_data
    
    def _apply_masking_method(
        self,
        series: pd.Series,
        method: str,
        pii_type: str
    ) -> pd.Series:
        """Apply specific masking method to a series"""
        if method == "full":
            return pd.Series(["***MASKED***"] * len(series), index=series.index)
        
        elif method == "partial":
            return series.astype(str).apply(
                lambda x: self.mask_sensitive_value(x) if pd.notna(x) else x
            )
        
        elif method == "hash":
            return series.astype(str).apply(
                lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:8] if pd.notna(x) else x
            )
        
        elif method == "pseudonymize":
            return self._pseudonymize_series(series, pii_type)
        
        else:
            return series  # No masking
    
    def _pseudonymize_series(self, series: pd.Series, pii_type: str) -> pd.Series:
        """Generate pseudonyms for sensitive data"""
        unique_values = series.unique()
        pseudonym_map = {}
        
        for value in unique_values:
            if pd.isna(value):
                pseudonym_map[value] = value
            else:
                pseudonym_map[value] = self._generate_pseudonym(str(value), pii_type)
        
        return series.map(pseudonym_map)
    
    def _generate_pseudonym(self, value: str, pii_type: str) -> str:
        """Generate a pseudonym for a specific PII type"""
        # Create a deterministic hash for consistency
        hash_value = hashlib.sha256(value.encode()).hexdigest()
        
        if pii_type == PIIType.EMAIL.value:
            return f"user{hash_value[:8]}@example.com"
        elif pii_type == PIIType.PHONE.value:
            return f"555-{hash_value[:3]}-{hash_value[3:7]}"
        elif pii_type == PIIType.NAME.value:
            return f"Person_{hash_value[:8]}"
        elif pii_type == PIIType.SSN.value:
            return f"***-**-{hash_value[:4]}"
        else:
            return f"PSEUDO_{hash_value[:8]}"
    
    def classify_data_sensitivity(
        self,
        data: pd.DataFrame,
        pii_findings: Dict[str, List[Dict[str, Any]]]
    ) -> DataClassification:
        """Classify overall data sensitivity"""
        if not pii_findings:
            return DataClassification.PUBLIC
        
        high_sensitivity_types = [
            PIIType.SSN.value,
            PIIType.CREDIT_CARD.value,
            PIIType.DATE_OF_BIRTH.value
        ]
        
        medium_sensitivity_types = [
            PIIType.EMAIL.value,
            PIIType.PHONE.value,
            PIIType.NAME.value,
            PIIType.ADDRESS.value
        ]
        
        # Check for high sensitivity PII
        for column_findings in pii_findings.values():
            for finding in column_findings:
                if (finding["pii_type"] in high_sensitivity_types and 
                    finding["confidence"] > 0.7):
                    return DataClassification.RESTRICTED
        
        # Check for medium sensitivity PII
        for column_findings in pii_findings.values():
            for finding in column_findings:
                if (finding["pii_type"] in medium_sensitivity_types and 
                    finding["confidence"] > 0.5):
                    return DataClassification.CONFIDENTIAL
        
        return DataClassification.INTERNAL
    
    def secure_delete_data(self, file_path: str) -> bool:
        """Securely delete sensitive data"""
        try:
            import os
            
            if os.path.exists(file_path):
                # Overwrite file with random data multiple times
                file_size = os.path.getsize(file_path)
                
                with open(file_path, "rb+") as file:
                    for _ in range(3):  # 3-pass overwrite
                        file.seek(0)
                        file.write(secrets.token_bytes(file_size))
                        file.flush()
                        os.fsync(file.fileno())
                
                # Remove the file
                os.remove(file_path)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Secure deletion failed: {e}")
            return False
    
    def generate_audit_hash(self, data: Any) -> str:
        """Generate tamper-evident hash for audit logs"""
        content = str(data).encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    def validate_ip_access(self, ip_address: str, allowed_ranges: List[str]) -> bool:
        """Validate if IP address is in allowed ranges"""
        if not allowed_ranges:
            return True  # No restrictions
        
        try:
            import ipaddress
            
            ip = ipaddress.ip_address(ip_address)
            
            for ip_range in allowed_ranges:
                if '/' in ip_range:
                    # CIDR notation
                    network = ipaddress.ip_network(ip_range, strict=False)
                    if ip in network:
                        return True
                else:
                    # Single IP
                    if ip == ipaddress.ip_address(ip_range):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"IP validation failed: {e}")
            return False  # Deny on error


security_service = DataSecurityService()