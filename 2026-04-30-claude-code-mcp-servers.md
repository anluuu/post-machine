# Claude Code MCP Servers: What I'm Using in 2026

MCP (Model Context Protocol) servers are how Claude Code connects to external tools. Here's my setup:

**Essential Tier (I use daily):**
- **GitHub** - Create PRs, manage issues, review code
- **Filesystem** - Access files outside current project
- **PostgreSQL** - Query databases, explore schemas

**Productivity Tier (saves time):**
- **Slack** - Send updates, read channels
- **Linear** - Create issues, manage projects
- **Notion** - Read/write pages and databases

**Infrastructure Tier (what I do at work):**
- **Docker** - Manage containers
- **Kubernetes** - Query clusters, read logs
- **Terraform** - Manage infrastructure state

**Data & Search (game changers):**
- **BigQuery** - Analytics queries from Claude
- **Context7** - Up-to-date library docs
- **Brave Search** - Web search with citations

**Configuration is easy:**
- CLI: `claude mcp add github --scope user --transport http`
- Manual: Edit `~/.claude/mcp.json` or `.mcp.json`

**2026 improvements:**
- Tool Search fetches only relevant tools (reduces context bloat)
- Scope system: local, project, and user-level configs
- Per-project servers for different needs

I use Claude Code 10+ hours/day. The MCP servers are why it feels like an extension of my workflow, not just a chatbot.

#ClaudeCode #MCP #DeveloperTools
