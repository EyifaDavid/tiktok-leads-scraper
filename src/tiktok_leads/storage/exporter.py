"""Data export utilities for leads."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

from tiktok_leads.models.lead import Lead
from tiktok_leads.exceptions import ExportError

logger = logging.getLogger(__name__)


class Exporter:
    """Export leads to various formats."""
    
    def __init__(self, output_dir: str):
        """Initialize exporter.
        
        Args:
            output_dir: Directory to save exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, prefix: str, extension: str) -> str:
        """Generate timestamped filename.
        
        Args:
            prefix: Filename prefix
            extension: File extension
        
        Returns:
            Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"

    def to_csv(self, leads: List[Lead], filename: Optional[str] = None) -> str:
        """Export leads to CSV file.
        
        Args:
            leads: List of Lead objects
            filename: Optional custom filename
        
        Returns:
            Path to exported file
        """
        if not leads:
            logger.warning("No leads to export")
            return ""
        
        try:
            # Convert leads to dictionaries
            data = []
            for lead in leads:
                lead_dict = lead.model_dump()
                if lead_dict.get("id") is not None:
                    del lead_dict["id"]
                if lead_dict.get("scraped_at"):
                    lead_dict["scraped_at"] = str(lead_dict["scraped_at"])
                data.append(lead_dict)
            
            # Create DataFrame and export
            df = pd.DataFrame(data)
            
            if not filename:
                filename = self._generate_filename("tiktok_leads", "csv")
            
            filepath = self.output_dir / filename
            df.to_csv(filepath, index=False, encoding="utf-8")
            
            logger.info(f"Exported {len(leads)} leads to {filepath}")
            return str(filepath)
        except Exception as e:
            raise ExportError(f"Failed to export to CSV: {e}") from e

    def to_json(self, leads: List[Lead], filename: Optional[str] = None) -> str:
        """Export leads to JSON file.
        
        Args:
            leads: List of Lead objects
            filename: Optional custom filename
        
        Returns:
            Path to exported file
        """
        if not leads:
            logger.warning("No leads to export")
            return ""
        
        try:
            # Convert leads to dictionaries
            data = []
            for lead in leads:
                lead_dict = lead.model_dump()
                if lead_dict.get("id") is not None:
                    del lead_dict["id"]
                if lead_dict.get("scraped_at"):
                    lead_dict["scraped_at"] = str(lead_dict["scraped_at"])
                data.append(lead_dict)
            
            if not filename:
                filename = self._generate_filename("tiktok_leads", "json")
            
            filepath = self.output_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(leads)} leads to {filepath}")
            return str(filepath)
        except Exception as e:
            raise ExportError(f"Failed to export to JSON: {e}") from e

    def to_excel(self, leads: List[Lead], filename: Optional[str] = None) -> str:
        """Export leads to Excel file.
        
        Args:
            leads: List of Lead objects
            filename: Optional custom filename
        
        Returns:
            Path to exported file
        """
        if not leads:
            logger.warning("No leads to export")
            return ""
        
        try:
            # Convert leads to dictionaries
            data = []
            for lead in leads:
                lead_dict = lead.model_dump()
                if lead_dict.get("id") is not None:
                    del lead_dict["id"]
                if lead_dict.get("scraped_at"):
                    lead_dict["scraped_at"] = str(lead_dict["scraped_at"])
                data.append(lead_dict)
            
            # Create DataFrame and export
            df = pd.DataFrame(data)
            
            if not filename:
                filename = self._generate_filename("tiktok_leads", "xlsx")
            
            filepath = self.output_dir / filename
            df.to_excel(filepath, index=False, engine="openpyxl")
            
            logger.info(f"Exported {len(leads)} leads to {filepath}")
            return str(filepath)
        except Exception as e:
            raise ExportError(f"Failed to export to Excel: {e}") from e

    def get_export_summary(self, leads: List[Lead]) -> dict:
        """Get summary statistics of leads.
        
        Args:
            leads: List of Lead objects
        
        Returns:
            Summary dictionary
        """
        total = len(leads)
        with_email = sum(1 for lead in leads if lead.has_email())
        with_phone = sum(1 for lead in leads if lead.has_phone())
        with_contact = sum(1 for lead in leads if lead.has_contact_info())
        
        return {
            "total_leads": total,
            "with_email": with_email,
            "with_phone": with_phone,
            "with_any_contact": with_contact,
            "email_rate": f"{(with_email/total*100):.1f}%" if total > 0 else "0%",
            "phone_rate": f"{(with_phone/total*100):.1f}%" if total > 0 else "0%",
        }
