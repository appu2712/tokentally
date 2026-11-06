import unittest
from tokentally.mcp import MCPServer, TOOLS_METADATA


class TestMCP(unittest.TestCase):
    def setUp(self):
        self.server = MCPServer()

    def test_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        res = self.server.handle_request(req)
        self.assertEqual(res["result"]["serverInfo"]["name"], "tokentally-mcp")

    def test_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        res = self.server.handle_request(req)
        tools = res["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("tokentally_estimate_cost", tool_names)
        self.assertIn("tokentally_compare_models", tool_names)

    def test_tools_call_estimate(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "tokentally_estimate_cost",
                "arguments": {"prompt": "Testing MCP server", "model": "gpt-4o"}
            }
        }
        res = self.server.handle_request(req)
        self.assertFalse(res["result"].get("isError", False))
        self.assertIn("total_cost_usd", res["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
