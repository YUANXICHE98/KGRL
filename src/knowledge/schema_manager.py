"""
Schema Manager for KGRL research framework.

Handles schema definition, validation, and evolution for knowledge graphs.
"""

from typing import Dict, Any, List, Optional, Set
import logging


class SchemaManager:
    """
    Schema management system for knowledge graphs.
    
    Supports:
    - Schema definition and validation
    - Entity type management
    - Relation type management
    - Schema evolution and migration
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the schema manager."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Schema configuration
        self.strict_validation = config.get("strict_validation", True)
        self.allow_schema_evolution = config.get("allow_schema_evolution", True)
        
        # Initialize schema
        self.entity_types = {}
        self.relation_types = {}
        self.constraints = {}
        
        self._load_initial_schema()
        
        self.logger.info("Schema manager initialized")
    
    def _load_initial_schema(self):
        """Load initial schema from configuration."""
        schema_config = self.config.get("schema", {})
        
        # Load entity types
        entity_types = schema_config.get("entity_types", {})
        for entity_type, definition in entity_types.items():
            self.define_entity_type(entity_type, definition)
        
        # Load relation types
        relation_types = schema_config.get("relation_types", {})
        for relation_type, definition in relation_types.items():
            self.define_relation_type(relation_type, definition)
        
        # Load constraints
        constraints = schema_config.get("constraints", {})
        for constraint_name, definition in constraints.items():
            self.add_constraint(constraint_name, definition)
    
    def define_entity_type(self, entity_type: str, definition: Dict[str, Any]) -> bool:
        """
        Define a new entity type.
        
        Args:
            entity_type: Name of the entity type
            definition: Entity type definition
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate definition
            required_fields = ["properties", "description"]
            for field in required_fields:
                if field not in definition:
                    raise ValueError(f"Missing required field: {field}")
            
            # Store entity type
            self.entity_types[entity_type] = {
                "properties": definition["properties"],
                "description": definition["description"],
                "required_properties": definition.get("required_properties", []),
                "parent_types": definition.get("parent_types", []),
                "created_at": self._get_timestamp()
            }
            
            self.logger.info(f"Defined entity type: {entity_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to define entity type {entity_type}: {e}")
            return False
    
    def define_relation_type(self, relation_type: str, definition: Dict[str, Any]) -> bool:
        """
        Define a new relation type.
        
        Args:
            relation_type: Name of the relation type
            definition: Relation type definition
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate definition
            required_fields = ["source_types", "target_types", "description"]
            for field in required_fields:
                if field not in definition:
                    raise ValueError(f"Missing required field: {field}")
            
            # Store relation type
            self.relation_types[relation_type] = {
                "source_types": definition["source_types"],
                "target_types": definition["target_types"],
                "description": definition["description"],
                "properties": definition.get("properties", {}),
                "cardinality": definition.get("cardinality", "many-to-many"),
                "created_at": self._get_timestamp()
            }
            
            self.logger.info(f"Defined relation type: {relation_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to define relation type {relation_type}: {e}")
            return False
    
    def validate_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an entity against the schema.
        
        Args:
            entity: Entity to validate
            
        Returns:
            Validation result
        """
        try:
            entity_type = entity.get("type")
            if not entity_type:
                return {"valid": False, "errors": ["Missing entity type"]}
            
            if entity_type not in self.entity_types:
                if self.strict_validation:
                    return {"valid": False, "errors": [f"Unknown entity type: {entity_type}"]}
                else:
                    # Auto-create entity type if schema evolution is allowed
                    if self.allow_schema_evolution:
                        self._auto_create_entity_type(entity_type, entity)
            
            # Validate properties
            type_def = self.entity_types.get(entity_type, {})
            validation_result = self._validate_entity_properties(entity, type_def)
            
            return validation_result
            
        except Exception as e:
            return {"valid": False, "errors": [f"Validation error: {e}"]}
    
    def validate_relation(self, relation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a relation against the schema.
        
        Args:
            relation: Relation to validate
            
        Returns:
            Validation result
        """
        try:
            relation_type = relation.get("type")
            if not relation_type:
                return {"valid": False, "errors": ["Missing relation type"]}
            
            if relation_type not in self.relation_types:
                if self.strict_validation:
                    return {"valid": False, "errors": [f"Unknown relation type: {relation_type}"]}
                else:
                    # Auto-create relation type if schema evolution is allowed
                    if self.allow_schema_evolution:
                        self._auto_create_relation_type(relation_type, relation)
            
            # Validate source and target types
            type_def = self.relation_types.get(relation_type, {})
            validation_result = self._validate_relation_types(relation, type_def)
            
            return validation_result
            
        except Exception as e:
            return {"valid": False, "errors": [f"Validation error: {e}"]}
    
    def _validate_entity_properties(self, entity: Dict[str, Any], type_def: Dict[str, Any]) -> Dict[str, Any]:
        """Validate entity properties against type definition."""
        errors = []
        warnings = []
        
        entity_properties = entity.get("properties", {})
        defined_properties = type_def.get("properties", {})
        required_properties = type_def.get("required_properties", [])
        
        # Check required properties
        for required_prop in required_properties:
            if required_prop not in entity_properties:
                errors.append(f"Missing required property: {required_prop}")
        
        # Check property types
        for prop_name, prop_value in entity_properties.items():
            if prop_name in defined_properties:
                expected_type = defined_properties[prop_name].get("type")
                if expected_type and not self._check_property_type(prop_value, expected_type):
                    errors.append(f"Property {prop_name} has wrong type")
            else:
                warnings.append(f"Unknown property: {prop_name}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_relation_types(self, relation: Dict[str, Any], type_def: Dict[str, Any]) -> Dict[str, Any]:
        """Validate relation source and target types."""
        errors = []
        
        source_type = relation.get("source_type")
        target_type = relation.get("target_type")
        
        allowed_source_types = type_def.get("source_types", [])
        allowed_target_types = type_def.get("target_types", [])
        
        if source_type and allowed_source_types and source_type not in allowed_source_types:
            errors.append(f"Invalid source type: {source_type}")
        
        if target_type and allowed_target_types and target_type not in allowed_target_types:
            errors.append(f"Invalid target type: {target_type}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": []
        }
    
    def _auto_create_entity_type(self, entity_type: str, entity: Dict[str, Any]):
        """Auto-create entity type from example entity."""
        properties = {}
        entity_properties = entity.get("properties", {})
        
        for prop_name, prop_value in entity_properties.items():
            properties[prop_name] = {
                "type": type(prop_value).__name__,
                "description": f"Auto-generated property for {prop_name}"
            }
        
        definition = {
            "properties": properties,
            "description": f"Auto-generated entity type for {entity_type}",
            "required_properties": [],
            "auto_generated": True
        }
        
        self.define_entity_type(entity_type, definition)
    
    def _auto_create_relation_type(self, relation_type: str, relation: Dict[str, Any]):
        """Auto-create relation type from example relation."""
        definition = {
            "source_types": [relation.get("source_type", "any")],
            "target_types": [relation.get("target_type", "any")],
            "description": f"Auto-generated relation type for {relation_type}",
            "properties": {},
            "cardinality": "many-to-many",
            "auto_generated": True
        }
        
        self.define_relation_type(relation_type, definition)
    
    def _check_property_type(self, value: Any, expected_type: str) -> bool:
        """Check if property value matches expected type."""
        type_mapping = {
            "string": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict
        }
        
        expected_python_type = type_mapping.get(expected_type.lower())
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, assume valid
    
    def add_constraint(self, constraint_name: str, definition: Dict[str, Any]) -> bool:
        """Add a schema constraint."""
        try:
            self.constraints[constraint_name] = {
                "type": definition.get("type", "custom"),
                "description": definition.get("description", ""),
                "rules": definition.get("rules", {}),
                "created_at": self._get_timestamp()
            }
            
            self.logger.info(f"Added constraint: {constraint_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add constraint {constraint_name}: {e}")
            return False
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get a summary of the current schema."""
        return {
            "entity_types": list(self.entity_types.keys()),
            "relation_types": list(self.relation_types.keys()),
            "constraints": list(self.constraints.keys()),
            "total_entity_types": len(self.entity_types),
            "total_relation_types": len(self.relation_types),
            "total_constraints": len(self.constraints),
            "strict_validation": self.strict_validation,
            "allow_schema_evolution": self.allow_schema_evolution
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def cleanup(self):
        """Clean up schema manager resources."""
        pass
