"""
Connection Validation Utilities for Airflow DAGs

This module provides utilities to validate that required connections are available
before DAG execution begins. This helps prevent DAG failures due to missing connections.
"""

import logging
from typing import List, Dict, Any, Optional

from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook


logger = logging.getLogger(__name__)


class ConnectionValidator:
    """Validates that required Airflow connections are available and accessible"""
    
    def __init__(self, required_connections: List[str]):
        """
        Initialize validator with list of required connection IDs
        
        Args:
            required_connections: List of connection IDs that must be available
        """
        self.required_connections = required_connections
        self.validation_results: Dict[str, Dict[str, Any]] = {}
    
    def validate_all_connections(self, raise_on_failure: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Validate all required connections
        
        Args:
            raise_on_failure: Whether to raise exception if any connection fails
            
        Returns:
            Dictionary with validation results for each connection
            
        Raises:
            AirflowException: If raise_on_failure=True and any connection is invalid
        """
        logger.info(f"Validating {len(self.required_connections)} required connections...")
        
        failed_connections = []
        
        for conn_id in self.required_connections:
            result = self.validate_connection(conn_id, raise_on_failure=False)
            self.validation_results[conn_id] = result
            
            if not result['is_valid']:
                failed_connections.append(conn_id)
                logger.error(f"Connection validation failed for {conn_id}: {result['error']}")
            else:
                logger.info(f"✓ Connection {conn_id} validated successfully")
        
        # Summary logging
        valid_count = len(self.required_connections) - len(failed_connections)
        logger.info(f"Connection validation summary: {valid_count}/{len(self.required_connections)} connections valid")
        
        if failed_connections and raise_on_failure:
            raise AirflowException(
                f"Connection validation failed for: {', '.join(failed_connections)}. "
                f"Check Airflow connections configuration."
            )
        
        return self.validation_results
    
    def validate_connection(self, conn_id: str, raise_on_failure: bool = True) -> Dict[str, Any]:
        """
        Validate a single connection
        
        Args:
            conn_id: Connection ID to validate
            raise_on_failure: Whether to raise exception on failure
            
        Returns:
            Dictionary with validation results
            
        Raises:
            AirflowException: If raise_on_failure=True and connection is invalid
        """
        result = {
            'conn_id': conn_id,
            'is_valid': False,
            'connection_type': None,
            'host': None,
            'port': None,
            'schema': None,
            'login': None,
            'error': None,
            'uri_masked': None
        }
        
        try:
            logger.info(f"Validating connection: {conn_id}")
            
            # Attempt to retrieve connection
            connection = BaseHook.get_connection(conn_id)
            
            # Extract connection details
            result.update({
                'is_valid': True,
                'connection_type': connection.conn_type,
                'host': connection.host,
                'port': connection.port,
                'schema': connection.schema,
                'login': connection.login,
                'uri_masked': self._mask_uri(connection.get_uri()) if connection else None
            })
            
            logger.info(f"✓ Connection {conn_id} details: type={connection.conn_type}, host={connection.host}")
            
        except Exception as e:
            error_msg = f"Failed to retrieve connection {conn_id}: {str(e)}"
            result['error'] = error_msg
            logger.error(error_msg)
            
            if raise_on_failure:
                raise AirflowException(error_msg)
        
        return result
    
    def _mask_uri(self, uri: str) -> str:
        """
        Mask password in URI for logging
        
        Args:
            uri: Connection URI
            
        Returns:
            URI with password masked
        """
        if not uri:
            return uri
            
        # Simple password masking - replace everything between :// and @ with ***
        import re
        pattern = r'(:\/\/[^:]*:)([^@]*)(@)'
        return re.sub(pattern, r'\1***\3', uri)
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """
        Get summary of connection validation results
        
        Returns:
            Summary dictionary with counts and status
        """
        if not self.validation_results:
            return {'message': 'No validations performed yet'}
        
        total = len(self.validation_results)
        valid = sum(1 for result in self.validation_results.values() if result['is_valid'])
        invalid = total - valid
        
        return {
            'total_connections': total,
            'valid_connections': valid,
            'invalid_connections': invalid,
            'success_rate': f"{(valid/total)*100:.1f}%" if total > 0 else "0%",
            'all_valid': invalid == 0
        }


def validate_dag_connections(required_connections: List[str], task_name: str = "validate_connections") -> Dict[str, Any]:
    """
    Convenience function to validate connections for a DAG
    
    Args:
        required_connections: List of connection IDs to validate
        task_name: Name of the task performing validation (for logging)
        
    Returns:
        Validation results dictionary
        
    Raises:
        AirflowException: If any required connection is invalid
    """
    logger.info(f"[{task_name}] Starting connection validation...")
    
    validator = ConnectionValidator(required_connections)
    results = validator.validate_all_connections(raise_on_failure=True)
    summary = validator.get_connection_summary()
    
    logger.info(f"[{task_name}] Connection validation completed: {summary}")
    
    return {
        'validation_results': results,
        'summary': summary,
        'task_name': task_name
    }


# Standard connection sets for common DAG patterns
POSTGRES_CONNECTIONS = ["postgres_default"]
STANDARD_PIPELINE_CONNECTIONS = ["postgres_default"]
TEST_CONNECTIONS = ["postgres_default"]
