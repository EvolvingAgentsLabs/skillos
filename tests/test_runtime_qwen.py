"""
Tests for the Agent runtime (QWEN.md manifest + agent_runtime.py).

Covers:
  - QWEN.md has mandatory boot requirement referencing Boot.md
  - Tool call format is valid XML
  - Required native tools are defined
  - agent_runtime.py loads manifest and compiles tools
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

    def test_agent_runtime_py_exists(self, root):
        assert (root / "agent_runtime.py").exists()


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


# ── agent_runtime.py module tests ─────────────────────────────────

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


# ── GEMINI.md manifest loader tests ─────────────────────────────

class TestGeminiManifestLoader:
    """Verify that _load_manifest correctly parses GEMINI.md shell-based tools."""

    @pytest.fixture(scope="class")
    def gemini_rt(self, root):
        mod = load_qwen_module()
        with patch.dict(sys.modules, {"openai": MagicMock(), "dotenv": MagicMock()}):
            from sandbox import create_executor
            rt = object.__new__(mod.AgentRuntime)
            rt.client = MagicMock()
            rt.model = "test-model"
            rt.tools = {}
            rt.system_prompt = ""
            rt.executor = create_executor("local")
            rt._load_manifest(str(root / "GEMINI.md"))
        return rt

    def test_system_prompt_populated(self, gemini_rt):
        assert len(gemini_rt.system_prompt) > 100

    def test_shell_tools_loaded(self, gemini_rt):
        """Core shell tools from GEMINI.md must be wrapped as callables."""
        for tool in ["read_file", "write_file", "list_files", "web_fetch"]:
            assert tool in gemini_rt.tools, f"Tool '{tool}' not loaded from GEMINI.md"
            assert callable(gemini_rt.tools[tool])

    def test_delegate_mapped(self, gemini_rt):
        """run_agent in GEMINI.md must be mapped to delegate_to_agent."""
        assert callable(gemini_rt.tools.get("delegate_to_agent"))

    def test_call_llm_available(self, gemini_rt):
        assert callable(gemini_rt.tools.get("call_llm"))

    def test_provider_default_manifest(self):
        """Each provider config must include a default manifest path."""
        mod = load_qwen_module()
        for provider, cfg in mod.AgentRuntime.PROVIDER_CONFIGS.items():
            assert "manifest" in cfg, f"Provider '{provider}' missing 'manifest' key"


# ── Gemma provider config tests ──────────────────────────────────

class TestGemmaProviderConfig:
    """Verify the gemma provider is correctly configured in PROVIDER_CONFIGS."""

    @pytest.fixture(scope="class")
    def gemma_cfg(self):
        mod = load_qwen_module()
        return mod.AgentRuntime.PROVIDER_CONFIGS

    def test_gemma_provider_exists(self, gemma_cfg):
        assert "gemma" in gemma_cfg, "PROVIDER_CONFIGS must include 'gemma'"

    def test_gemma_uses_gemini_manifest(self, gemma_cfg):
        assert gemma_cfg["gemma"]["manifest"] == "GEMINI.md"

    def test_gemma_has_base_url_env_key(self, gemma_cfg):
        assert gemma_cfg["gemma"]["base_url_env"] == "OLLAMA_BASE_URL"

    def test_gemma_has_model_env_key(self, gemma_cfg):
        assert gemma_cfg["gemma"]["model_env"] == "GEMMA_MODEL"

    def test_gemma_default_model(self, gemma_cfg):
        assert gemma_cfg["gemma"]["model"] == "gemma4"

    def test_gemma_api_key_default(self, gemma_cfg):
        assert gemma_cfg["gemma"]["api_key_default"] == "ollama"


# ── Gemma OpenRouter provider config tests ────────────────────────

class TestGemmaOpenRouterProviderConfig:
    """Verify the gemma-openrouter provider is correctly configured."""

    @pytest.fixture(scope="class")
    def provider_configs(self):
        mod = load_qwen_module()
        return mod.AgentRuntime.PROVIDER_CONFIGS

    def test_provider_exists(self, provider_configs):
        assert "gemma-openrouter" in provider_configs

    def test_uses_openrouter_base_url(self, provider_configs):
        assert provider_configs["gemma-openrouter"]["base_url"] == "https://openrouter.ai/api/v1"

    def test_uses_openrouter_api_key(self, provider_configs):
        assert provider_configs["gemma-openrouter"]["api_key_env"] == "OPENROUTER_API_KEY"

    def test_default_model(self, provider_configs):
        assert provider_configs["gemma-openrouter"]["model"] == "google/gemma-4-26b-a4b-it"

    def test_uses_gemini_manifest(self, provider_configs):
        assert provider_configs["gemma-openrouter"]["manifest"] == "GEMINI.md"

    def test_has_model_env_override(self, provider_configs):
        assert provider_configs["gemma-openrouter"]["model_env"] == "GEMMA_OPENROUTER_MODEL"

    def test_has_cache_headers(self, provider_configs):
        headers = provider_configs["gemma-openrouter"]["cache_headers"]
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers

    def test_manifest_loads_for_gemma_openrouter(self, root):
        """Verify GEMINI.md manifest loads correctly for gemma-openrouter."""
        mod = load_qwen_module()
        with patch.dict(sys.modules, {"openai": MagicMock(), "dotenv": MagicMock()}):
            from sandbox import create_executor
            rt = object.__new__(mod.AgentRuntime)
            rt.client = MagicMock()
            rt.model = "google/gemma-4-26b-a4b-it"
            rt.tools = {}
            rt.system_prompt = ""
            rt.executor = create_executor("local")
            rt._load_manifest(str(root / "GEMINI.md"))
        assert len(rt.system_prompt) > 100
        assert callable(rt.tools.get("delegate_to_agent"))
