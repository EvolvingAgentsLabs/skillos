"""
Tests for the QWEN runtime (QWEN.md manifest + qwen_runtime.py).

Covers:
  - QWEN.md has mandatory boot requirement referencing Boot.md
  - Tool call format is valid XML
  - Required native tools are defined
  - qwen_runtime.py loads manifest and compiles tools
  - Tool names match what Boot.md and QWEN.md promise
"""

import re
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from conftest import ROOT, load_qwen_module, has_section, extract_section


# ── QWEN.md structural tests ──────────────────────────────────────

class TestQwenManifestExists:
    def test_qwen_md_exists(self, root):
        assert (root / "QWEN.md").exists()

    def test_qwen_md_not_empty(self, qwen_md_text):
        assert len(qwen_md_text.strip()) > 200

    def test_qwen_runtime_py_exists(self, root):
        assert (root / "qwen_runtime.py").exists()


class TestQwenBootRequirement:
    """QWEN.md must instruct the runtime to read Boot.md first."""

    def test_boot_requirement_section_exists(self, qwen_md_text):
        assert "BOOT REQUIREMENT" in qwen_md_text or "Boot.md" in qwen_md_text[:500], (
            "QWEN.md must reference Boot.md near the top as a boot requirement"
        )

    def test_read_boot_md_tool_call_present(self, qwen_md_text):
        """The manifest must contain an explicit read_file('Boot.md') call."""
        assert 'Boot.md' in qwen_md_text
        # Check there is a tool_call block for read_file + Boot.md
        pattern = re.compile(
            r'<tool_call\s+name="read_file">.*?Boot\.md.*?</tool_call>',
            re.DOTALL,
        )
        assert pattern.search(qwen_md_text), (
            "QWEN.md must contain a <tool_call name='read_file'> for Boot.md"
        )

    def test_boot_requirement_is_before_system_prompt(self, qwen_md_text):
        """Boot requirement must appear before the main QWEN system prompt body."""
        boot_pos = qwen_md_text.find("Boot.md")
        agent_pos = qwen_md_text.find("SystemAgent")
        assert boot_pos < agent_pos, (
            "Boot.md reference must appear before the SystemAgent instructions"
        )


class TestQwenManifestStructure:
    def test_has_native_tools_section(self, qwen_md_text):
        assert "### NATIVE TOOLS" in qwen_md_text

    def test_has_execution_flow_section(self, qwen_md_text):
        assert "EXECUTION FLOW" in qwen_md_text or "execution flow" in qwen_md_text.lower()

    def test_has_final_answer_format(self, qwen_md_text):
        assert "<final_answer>" in qwen_md_text

    def test_has_tool_call_format(self, qwen_md_text):
        assert "<tool_call" in qwen_md_text

    def test_tool_call_uses_name_attribute(self, qwen_md_text):
        assert 'tool_call name=' in qwen_md_text


class TestQwenNativeTools:
    """QWEN.md must define all required native tools."""

    REQUIRED_TOOLS = [
        "call_llm",
        "read_file",
        "write_file",
        "list_files",
        "execute_bash",
        "web_fetch",
        "grep_files",
        "create_agent",
        "delegate_to_agent",
        "list_agents",
        "load_agent",
        "query_memory_graph",
        "log_trace",
        "trigger_dream",
        "get_memory_stats",
        "robot_telemetry",
    ]

    @pytest.mark.parametrize("tool_name", REQUIRED_TOOLS)
    def test_tool_defined(self, qwen_md_text, tool_name):
        pattern = re.compile(rf'<tool\s+name="{re.escape(tool_name)}">', re.IGNORECASE)
        assert pattern.search(qwen_md_text), (
            f"QWEN.md is missing native tool definition: {tool_name}"
        )

    @pytest.mark.parametrize("tool_name", REQUIRED_TOOLS)
    def test_tool_has_description(self, qwen_md_text, tool_name):
        # Find the tool block and check it has a description
        block_pattern = re.compile(
            rf'<tool\s+name="{re.escape(tool_name)}">(.*?)</tool>',
            re.DOTALL,
        )
        m = block_pattern.search(qwen_md_text)
        assert m, f"Tool {tool_name} block not found"
        assert "<description>" in m.group(1), (
            f"Tool {tool_name} must have a <description> element"
        )

    @pytest.mark.parametrize("tool_name", REQUIRED_TOOLS)
    def test_tool_has_python_code(self, qwen_md_text, tool_name):
        block_pattern = re.compile(
            rf'<tool\s+name="{re.escape(tool_name)}">(.*?)</tool>',
            re.DOTALL,
        )
        m = block_pattern.search(qwen_md_text)
        assert m, f"Tool {tool_name} block not found"
        assert "<python_code>" in m.group(1), (
            f"Tool {tool_name} must have a <python_code> element"
        )


class TestQwenToolCallFormat:
    """All tool_call examples in QWEN.md must use valid XML-like format."""

    def test_tool_calls_have_closing_tag(self, qwen_md_text):
        opens = len(re.findall(r"<tool_call\b", qwen_md_text))
        closes = len(re.findall(r"</tool_call>", qwen_md_text))
        assert opens == closes, (
            f"Mismatched tool_call tags: {opens} open, {closes} close"
        )

    def test_tool_calls_contain_json_body(self, qwen_md_text):
        """Each tool_call block should contain JSON."""
        blocks = re.findall(
            r"<tool_call[^>]*>(.*?)</tool_call>",
            qwen_md_text,
            re.DOTALL,
        )
        for block in blocks:
            stripped = block.strip()
            if stripped:
                assert stripped.startswith("{"), (
                    f"tool_call body should be a JSON object, got: {stripped[:40]!r}"
                )


# ── qwen_runtime.py module tests ──────────────────────────────────

class TestQwenRuntimeModule:
    @pytest.fixture(scope="class")
    def qwen_mod(self):
        return load_qwen_module()

    def test_qwen_runtime_class_exists(self, qwen_mod):
        assert hasattr(qwen_mod, "QwenRuntime")

    def test_load_manifest_method_exists(self, qwen_mod):
        assert hasattr(qwen_mod.QwenRuntime, "_load_manifest")

    def test_handle_call_llm_method_exists(self, qwen_mod):
        assert hasattr(qwen_mod.QwenRuntime, "_handle_call_llm")

    def test_handle_delegate_method_exists(self, qwen_mod):
        assert hasattr(qwen_mod.QwenRuntime, "_handle_delegate_to_agent")

    def test_manifest_loads_system_prompt(self, qwen_mod, root):
        """QwenRuntime._load_manifest must populate system_prompt from QWEN.md."""
        with patch.dict(sys.modules, {"openai": MagicMock(), "dotenv": MagicMock()}):
            rt = object.__new__(qwen_mod.QwenRuntime)
            rt.client = MagicMock()
            rt.model = "test-model"
            rt.tools = {}
            rt.system_prompt = ""
            rt._load_manifest(str(root / "QWEN.md"))

        assert len(rt.system_prompt) > 100, "system_prompt should be populated"

    def test_manifest_compiles_core_tools(self, qwen_mod, root):
        """Core tools (read_file, write_file, etc.) must be compiled."""
        CORE_TOOLS = ["read_file", "write_file", "list_files", "execute_bash", "grep_files"]
        with patch.dict(sys.modules, {"openai": MagicMock(), "dotenv": MagicMock()}):
            rt = object.__new__(qwen_mod.QwenRuntime)
            rt.client = MagicMock()
            rt.model = "test-model"
            rt.tools = {}
            rt.system_prompt = ""
            rt._load_manifest(str(root / "QWEN.md"))

        for tool in CORE_TOOLS:
            assert tool in rt.tools, f"Tool '{tool}' was not compiled by _load_manifest"

    def test_special_tools_registered_as_callables(self, qwen_mod, root):
        """call_llm and delegate_to_agent must be registered as bound methods."""
        with patch.dict(sys.modules, {"openai": MagicMock(), "dotenv": MagicMock()}):
            rt = object.__new__(qwen_mod.QwenRuntime)
            rt.client = MagicMock()
            rt.model = "test-model"
            rt.tools = {}
            rt.system_prompt = ""
            rt._load_manifest(str(root / "QWEN.md"))

        assert callable(rt.tools.get("call_llm")), "call_llm must be callable"
        assert callable(rt.tools.get("delegate_to_agent")), (
            "delegate_to_agent must be callable"
        )
