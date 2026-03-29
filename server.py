import logging
import sys

from mcp.server.fastmcp import FastMCP

# Nom du serveur visible pour ia
mcp = FastMCP("video-control")
# Import des tools
from tools.video import play_series_episode
from tools.series import list_series

# Enregistrement des tools
mcp.tool()(play_series_episode)
mcp.tool()(list_series)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)  # ⚠️ important pour MCP
    ]
)

if __name__ == "__main__":
    mcp.run()