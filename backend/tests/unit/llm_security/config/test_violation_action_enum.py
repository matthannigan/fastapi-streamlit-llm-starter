"""
Test suite for ViolationAction enumeration.

Tests verify ViolationAction enum values and action levels according to the
public contract defined in config.pyi.
"""

import pytest


class TestViolationActionEnumValues:
    """Test ViolationAction enum member existence and values."""

    def test_violation_action_has_all_documented_members(self):
        """
        Test that ViolationAction enum includes all documented action types.

        Verifies:
            ViolationAction enum contains NONE, WARN, BLOCK, REDACT, and FLAG
            per contract's Available Actions section.

        Business Impact:
            Ensures all violation response strategies are available for security
            policy configuration.

        Scenario:
            Given: ViolationAction enum imported.
            When: Action type attributes are accessed.
            Then: All five action types exist with correct values.

        Fixtures Used:
            None - tests enum definition directly.
        """
        # Import the actual ViolationAction from the implementation
        from app.infrastructure.security.llm.config import ViolationAction

        # Verify all documented action types exist
        assert hasattr(ViolationAction, 'NONE')
        assert hasattr(ViolationAction, 'WARN')
        assert hasattr(ViolationAction, 'BLOCK')
        assert hasattr(ViolationAction, 'REDACT')
        assert hasattr(ViolationAction, 'FLAG')

        # Verify the values match the documented string values
        assert ViolationAction.NONE.value == "none"
        assert ViolationAction.WARN.value == "warn"
        assert ViolationAction.BLOCK.value == "block"
        assert ViolationAction.REDACT.value == "redact"
        assert ViolationAction.FLAG.value == "flag"

        # Verify we can iterate over all enum members
        all_actions = list(ViolationAction)
        assert len(all_actions) == 5

        # Verify all expected members are in the iteration
        action_values = [action.value for action in all_actions]
        expected_values = ["none", "warn", "block", "redact", "flag"]
        for expected in expected_values:
            assert expected in action_values

    def test_violation_action_enum_members_are_strings(self):
        """
        Test that ViolationAction enum values are string type.

        Verifies:
            ViolationAction inherits from str, Enum per contract's class declaration.

        Business Impact:
            Ensures action types can be serialized to configuration files and
            JSON responses.

        Scenario:
            Given: Any ViolationAction enum member.
            When: Type is checked.
            Then: Member is instance of str.

        Fixtures Used:
            None - tests enum type characteristics.
        """
        from app.infrastructure.security.llm.config import ViolationAction

        # Test that enum members are instances of str
        assert isinstance(ViolationAction.NONE, str)
        assert isinstance(ViolationAction.WARN, str)
        assert isinstance(ViolationAction.BLOCK, str)
        assert isinstance(ViolationAction.REDACT, str)
        assert isinstance(ViolationAction.FLAG, str)

        # Test that enum members are also instances of ViolationAction (enum behavior)
        assert isinstance(ViolationAction.NONE, ViolationAction)
        assert isinstance(ViolationAction.WARN, ViolationAction)
        assert isinstance(ViolationAction.BLOCK, ViolationAction)
        assert isinstance(ViolationAction.REDACT, ViolationAction)
        assert isinstance(ViolationAction.FLAG, ViolationAction)

        # Test that they can be used as strings (through .value property)
        action_str = ViolationAction.BLOCK.value
        assert action_str == "block"

        # Test that .value returns a regular string that can be manipulated
        assert ViolationAction.WARN.value.upper() == "WARN"
        assert ViolationAction.BLOCK.value.replace("block", "BLOCKED") == "BLOCKED"

        # Test that they maintain enum behavior
        assert ViolationAction("block") == ViolationAction.BLOCK
        assert ViolationAction("warn") == ViolationAction.WARN

    def test_violation_action_represents_severity_progression(self):
        """
        Test that ViolationAction enum values represent increasing intervention levels.

        Verifies:
            ViolationAction members progress from passive (NONE) to active (BLOCK)
            intervention per contract's Available Actions documentation.

        Business Impact:
            Enables graduated response policies where violation severity determines
            intervention level.

        Scenario:
            Given: ViolationAction enum members ordered by intervention level.
            When: Action levels are compared conceptually.
            Then: NONE < WARN < FLAG < REDACT < BLOCK in intervention intensity.

        Fixtures Used:
            None - tests enum semantic ordering.
        """
        from app.infrastructure.security.llm.config import ViolationAction

        # Define the expected intervention order based on documentation
        # NONE: No action, only log (least intervention)
        # WARN: Allow content but include warning metadata
        # FLAG: Mark content for manual review while allowing processing
        # REDACT: Remove or mask the problematic portions of the content
        # BLOCK: Completely prevent the content from being processed or delivered (most intervention)

        intervention_order = [
            ViolationAction.NONE,    # 0: Passive monitoring only
            ViolationAction.WARN,    # 1: Warning but allow content
            ViolationAction.FLAG,    # 2: Flag for review but allow content
            ViolationAction.REDACT,  # 3: Modify content by removing problematic parts
            ViolationAction.BLOCK    # 4: Complete content blocking
        ]

        # Verify we have all expected actions in the progression
        assert len(intervention_order) == 5
        assert all(action in intervention_order for action in ViolationAction)

        # Test that each action represents progressively more intervention
        # We'll test this conceptually through expected behavior characteristics

        # NONE should be the least intrusive - no content modification
        assert intervention_order.index(ViolationAction.NONE) == 0

        # BLOCK should be the most intrusive - complete content prevention
        assert intervention_order.index(ViolationAction.BLOCK) == 4

        # WARN should be less intrusive than FLAG (warning vs manual review)
        assert intervention_order.index(ViolationAction.WARN) < intervention_order.index(ViolationAction.FLAG)

        # FLAG should be less intrusive than REDACT (mark vs modify)
        assert intervention_order.index(ViolationAction.FLAG) < intervention_order.index(ViolationAction.REDACT)

        # REDACT should be less intrusive than BLOCK (modify vs block)
        assert intervention_order.index(ViolationAction.REDACT) < intervention_order.index(ViolationAction.BLOCK)

        # Test the complete ordering
        for i in range(len(intervention_order) - 1):
            current = intervention_order[i]
            next_action = intervention_order[i + 1]
            assert intervention_order.index(current) < intervention_order.index(next_action)

        # Verify practical usage scenarios that depend on this ordering
        def get_intervention_level(action):
            """Helper function to simulate intervention level logic."""
            return intervention_order.index(action)

        # Test that intervention levels can be used for decision making
        assert get_intervention_level(ViolationAction.NONE) == 0
        assert get_intervention_level(ViolationAction.BLOCK) == 4
        assert get_intervention_level(ViolationAction.WARN) < get_intervention_level(ViolationAction.BLOCK)
        assert get_intervention_level(ViolationAction.REDACT) > get_intervention_level(ViolationAction.WARN)


class TestViolationActionUsagePatterns:
    """Test ViolationAction enum usage in typical scenarios."""

    def test_violation_action_can_be_used_in_scanner_config(self, violation_action):
        """
        Test that ViolationAction members can be assigned to scanner configurations.

        Verifies:
            ViolationAction enums integrate with ScannerConfig for action policy
            specification per contract's Usage examples.

        Business Impact:
            Enables configuring scanner-specific response actions through enum
            values for type-safe configuration.

        Scenario:
            Given: ViolationAction member (e.g., BLOCK).
            When: Assigned to scanner configuration action field.
            Then: Configuration accepts and stores action type correctly.

        Fixtures Used:
            - violation_action: Fixture providing MockViolationAction instance.
        """
        from app.infrastructure.security.llm.config import ViolationAction, ScannerConfig

        # Test that ViolationAction can be used in ScannerConfig construction
        config_with_block = ScannerConfig(
            enabled=True,
            threshold=0.5,
            action=ViolationAction.BLOCK
        )
        assert config_with_block.action == ViolationAction.BLOCK
        assert config_with_block.action.value == "block"

        # Test with different action types
        config_with_warn = ScannerConfig(action=ViolationAction.WARN)
        assert config_with_warn.action == ViolationAction.WARN

        config_with_redact = ScannerConfig(action=ViolationAction.REDACT)
        assert config_with_redact.action == ViolationAction.REDACT

        config_with_flag = ScannerConfig(action=ViolationAction.FLAG)
        assert config_with_flag.action == ViolationAction.FLAG

        config_with_none = ScannerConfig(action=ViolationAction.NONE)
        assert config_with_none.action == ViolationAction.NONE

        # Test that action can be updated after creation (if supported by Pydantic)
        # Note: Since ScannerConfig uses Pydantic BaseModel, it's immutable by default
        # but we can test the creation aspect

        # Test that configuration serialization works with enum values
        config_dict = config_with_block.dict()
        assert config_dict['action'] == "block"  # Pydantic should serialize enum to string

        # Test that ViolationAction values work in configuration contexts
        # This simulates how they would be used in the security configuration system
        scanner_configs = {
            "strict": ScannerConfig(action=ViolationAction.BLOCK, threshold=0.3),
            "moderate": ScannerConfig(action=ViolationAction.WARN, threshold=0.7),
            "minimal": ScannerConfig(action=ViolationAction.FLAG, threshold=0.9)
        }

        # Verify each configuration stores the correct action
        assert scanner_configs["strict"].action == ViolationAction.BLOCK
        assert scanner_configs["moderate"].action == ViolationAction.WARN
        assert scanner_configs["minimal"].action == ViolationAction.FLAG

        # Test that configurations can be compared based on action types
        assert scanner_configs["strict"].action != scanner_configs["moderate"].action
        assert scanner_configs["moderate"].action == ViolationAction.WARN

        # Test the use case from contract documentation
        strict_config = ScannerConfig(
            action=ViolationAction.BLOCK,
            threshold=0.5
        )
        warn_config = ScannerConfig(
            action=ViolationAction.WARN,
            threshold=0.7
        )

        # Verify these configurations work as expected
        assert strict_config.action == ViolationAction.BLOCK
        assert warn_config.action == ViolationAction.WARN
        assert strict_config.threshold == 0.5
        assert warn_config.threshold == 0.7

        # Test the contract's example: Check if action requires content modification
        content_modifying_actions = [ViolationAction.BLOCK, ViolationAction.REDACT]
        config_block = ScannerConfig(action=ViolationAction.BLOCK)
        config_warn = ScannerConfig(action=ViolationAction.WARN)

        assert config_block.action in content_modifying_actions
        assert config_warn.action not in content_modifying_actions

    def test_violation_action_equality_with_string_values(self, violation_action):
        """
        Test that ViolationAction members can be compared with string values.

        Verifies:
            ViolationAction string inheritance allows comparison with plain strings
            for configuration validation.

        Business Impact:
            Enables flexible configuration parsing where string action values can
            be validated against enum members.

        Scenario:
            Given: ViolationAction member and equivalent string value.
            When: Equality comparison is performed.
            Then: Enum member equals corresponding string value.

        Fixtures Used:
            - violation_action: Fixture providing MockViolationAction instance.
        """
        from app.infrastructure.security.llm.config import ViolationAction

        # Test equality comparisons between enum members and string values
        assert ViolationAction.BLOCK == "block"
        assert ViolationAction.WARN == "warn"
        assert ViolationAction.REDACT == "redact"
        assert ViolationAction.FLAG == "flag"
        assert ViolationAction.NONE == "none"

        # Test that the equality is bidirectional
        assert "block" == ViolationAction.BLOCK
        assert "warn" == ViolationAction.WARN
        assert "redact" == ViolationAction.REDACT
        assert "flag" == ViolationAction.FLAG
        assert "none" == ViolationAction.NONE

        # Test inequality with different string values
        assert ViolationAction.BLOCK != "warn"
        assert ViolationAction.WARN != "block"
        assert ViolationAction.REDACT != "flag"
        assert ViolationAction.FLAG != "none"
        assert ViolationAction.NONE != "block"

        # Test that enum members are not equal to other enum members
        assert ViolationAction.BLOCK != ViolationAction.WARN
        assert ViolationAction.WARN != ViolationAction.REDACT
        assert ViolationAction.REDACT != ViolationAction.FLAG
        assert ViolationAction.FLAG != ViolationAction.NONE
        assert ViolationAction.NONE != ViolationAction.BLOCK

        # Test practical configuration validation scenarios
        def validate_action_string(action_str):
            """Simulate configuration validation with string input."""
            valid_actions = [ViolationAction.BLOCK, ViolationAction.WARN, ViolationAction.REDACT, ViolationAction.FLAG, ViolationAction.NONE]

            for action in valid_actions:
                if action == action_str:
                    return action
            return None

        # Test validation function with valid strings
        assert validate_action_string("block") == ViolationAction.BLOCK
        assert validate_action_string("warn") == ViolationAction.WARN
        assert validate_action_string("redact") == ViolationAction.REDACT
        assert validate_action_string("flag") == ViolationAction.FLAG
        assert validate_action_string("none") == ViolationAction.NONE

        # Test validation function with invalid strings
        assert validate_action_string("invalid") is None
        assert validate_action_string("BLOCK") is None  # Case sensitive
        assert validate_action_string("") is None

        # Test that string comparison works in conditional logic
        def get_action_description(action):
            """Helper function that uses string comparison."""
            if action == "none":
                return "No action taken"
            elif action == "warn":
                return "Warning issued"
            elif action == "flag":
                return "Content flagged for review"
            elif action == "redact":
                return "Problematic content redacted"
            elif action == "block":
                return "Content completely blocked"
            else:
                return "Unknown action"

        # Test the helper function with enum members
        assert get_action_description(ViolationAction.NONE) == "No action taken"
        assert get_action_description(ViolationAction.WARN) == "Warning issued"
        assert get_action_description(ViolationAction.FLAG) == "Content flagged for review"
        assert get_action_description(ViolationAction.REDACT) == "Problematic content redacted"
        assert get_action_description(ViolationAction.BLOCK) == "Content completely blocked"

        # Test that enum members can be used in string operations
        action_list = [ViolationAction.BLOCK, ViolationAction.WARN, ViolationAction.NONE]
        string_list = ["block", "warn", "none"]

        # Test that they can be compared and mixed in operations
        for action, expected_str in zip(action_list, string_list):
            assert action == expected_str
            assert action.value == expected_str
            assert action in string_list
            assert expected_str in [a.value for a in action_list]

        # Test JSON serialization/deserialization compatibility
        import json

        # Serialize enum to JSON
        config_data = {"action": ViolationAction.BLOCK}
        json_str = json.dumps(config_data)

        # Deserialize and compare
        parsed_data = json.loads(json_str)
        assert parsed_data["action"] == "block"
        assert ViolationAction.BLOCK == parsed_data["action"]