# Claude Code vs OpenCode — Skill 组装逻辑对比分析报告

## 一、总体架构对比

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code 组装流水线                         │
│                                                                 │
│  CLAUDE.md ──→ system-reminder 注入（user message 内）            │
│  Skill 文件 ──→ 按需加载，Skill 工具触发后注入（user message 内）  │
│  Agent 文件 ──→ Agent 工具触发，独立子会话                        │
│  工具声明 ──→ system message 中列出可用 skill 名称+描述           │
│                                                                 │
│  消息结构: [system] + [user(含CLAUDE.md+skill)] + [assistant]    │
│           + [user(tool_result)] + ...                           │
│  API: Anthropic Messages API                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    OpenCode 组装流水线                            │
│                                                                 │
│  system prompt ──→ 固定注入（agent-identity + Role + 行为指令）   │
│  Skill 文件 ──→ slash command 触发，内联注入（user message 内）   │
│  Skill 列表 ──→ system prompt 中列出可用 skill 名称              │
│  Skill 二次加载 ──→ assistant 调用 skill 工具，tool 返回内容      │
│                                                                 │
│  消息结构: [system(含Role+skill列表)] + [user(含skill内联)]       │
│           + [assistant(含reasoning)] + [tool] + ...             │
│  API: OpenAI Chat Completions API                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、Claude Code 组装逻辑详解

### 2.1 第一层：CLAUDE.md → system-reminder 注入

Claude Code 将 `CLAUDE.md` 的内容包装在 `<system-reminder>` 标签中，作为 **user message 的第一个 text block** 注入：

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "<system-reminder>\nAs you answer the user's questions, you can use the following context:\n# claudeMd\nCodebase and user instructions are shown below...\n\nContents of /home/rbtest0034/test/cc_test/bsc_str_lib-master/CLAUDE.md:\n\n# Working Principles\n## 1. Think Before Coding\n...\n## When to Load Other Skills\n- Non-trivial BSC change → load `/bsc-design` BEFORE planning.\n- Translating/porting C to BSC → load `/c-to-bsc` BEFORE starting.\n...\n"
    }
  ]
}
```

**关键特征**：
- CLAUDE.md 不是放在 `system` role 消息中，而是放在 `user` role 消息的 `<system-reminder>` 标签内
- CLAUDE.md 中包含**何时加载哪个 skill 的指引**（如 "Non-trivial BSC change → load `/bsc-design`"），这是**延迟加载策略**——skill 内容不预先注入，只在需要时加载

### 2.2 第二层：Skill 按需加载 → command-message 注入

用户输入 `/bsc-design` 命令后，Claude Code 将 skill 内容作为**独立的 text block** 注入同一 user message：

```json
{
  "type": "text",
  "text": "<command-message>bsc-design</command-message>\n<command-name>/bsc-design</command-name>\n<command-args>帮我基于此项目 继续开发出bsc的ftp服务器需求</command-args>\n"
},
{
  "type": "text",
  "text": "Base directory for this skill: /home/rbtest0034/test/cc_test/bsc_str_lib-master/.claude/skills/bsc-design\n\n# BiSheng C Design Skill\n\nBSC is not just \"C with annotations\" — the ownership system changes how APIs are shaped.\n..."
}
```

**关键特征**：
- Slash command 触发时，skill 的 SKILL.md **全文**被读取并注入为 user message 的新 text block
- 注入格式：先注入 `<command-message>` 元数据，再注入 skill 正文
- Skill 内容与用户输入在**同一个 user turn** 中，模型可以立即看到

### 2.3 第三层：Skill 列表预声明 → system message

Claude Code 在 system message 中列出所有可用 skill 的名称和描述：

```
The following skills are available for use with the Skill tool:

- bsc-borrowing: BiSheng C borrowing in the constrained subset...
- bsc-design: BiSheng C design and architecture decisions...
- bsc-ownership: BiSheng C ownership system in the constrained subset...
- bsc-invalid-sentinel: The INVALID-sentinel pattern for OOM-tolerant API design...
- superpowers:brainstorming: You MUST use this before any creative work...
...
```

**关键特征**：
- 只列出**名称+描述**，不列出 skill 全文（节省 token）
- 模型根据描述判断何时调用 `Skill` 工具加载具体内容
- 这是**目录索引**模式——先看目录，按需取内容

### 2.4 第四层：Assistant 响应 → tool_use 调用 Skill

Claude Code 的 assistant 响应使用 Anthropic 原生的 `tool_use` content block：

```json
{
  "type": "tool_use",
  "id": "toolu_01KXBHWyEPgy4SNFyERnNhxL",
  "name": "Skill",
  "input": {
    "skill": "superpowers:brainstorming"
  }
}
```

模型先调用 `Skill` 工具，Claude Code 客户端读取 SKILL.md 文件，将内容作为 `tool_result` 返回给模型。

### 2.5 Claude Code 完整组装流程图

```
用户输入 "/bsc-design 帮我基于此项目继续开发FTP服务器"
    │
    ▼
┌──────────────────────────────────────────┐
│ 1. CLAUDE.md 注入                         │
│    → <system-reminder> 包裹               │
│    → user message 第1个 text block        │
│    → 含 "何时加载 skill" 指引              │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ 2. Slash command 解析                     │
│    → <command-message> 元数据             │
│    → user message 第2个 text block        │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ 3. SKILL.md 全文注入                      │
│    → user message 第3个 text block        │
│    → "Base directory for this skill: ..." │
│    → bsc-design/SKILL.md 完整内容         │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ 4. Skill 目录索引（system message）        │
│    → 列出所有 skill 名称+描述             │
│    → 供模型后续按需加载                    │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ 5. 模型响应                               │
│    → 可能调用 Skill 工具加载更多 skill     │
│    → tool_use → tool_result 循环          │
│    → 可能调用 Agent 工具启动子代理         │
└──────────────────────────────────────────┘
```

---

## 三、OpenCode 组装逻辑详解

### 3.1 第一层：System Prompt 固定注入

OpenCode 使用**固定的 system role message**，包含 agent-identity、Role、Behavior_Instructions 等大量编排逻辑：

```json
{
  "role": "system",
  "content": "<agent-identity>\nYour designated identity for this session is \"Sisyphus\"...\n</agent-identity>\n<Role>\nYou are \"Sisyphus\" - Powerful AI Agent with orchestration capabilities...\n</Role>\n<Behavior_Instructions>\n## Phase 0 - Intent Gate (EVERY message)\n### Key Triggers...\n## Phase 1 - Codebase Assessment...\n## Phase 2A - Exploration & Research...\n...\n"
}
```

**关键特征**：
- system message 包含**完整的编排逻辑**（意图分类、代码库评估、探索研究、委托规则等）
- 这是 OpenCode 的"Sisyphus"编排层，与项目无关，是平台级指令
- Claude Code 没有等价的固定 system prompt——它的编排逻辑分散在 superpowers skill 中

### 3.2 第二层：Skill 列表内联注入

OpenCode 在 system prompt 中直接列出所有可用 skill：

```
⚡ YOUR SKILLS (PRIORITY): bsc-generic (project), bsc-borrowing (project), 
bsc-constexpr (project), bsc-errors (project), bsc-trait (project), 
bsc-coroutine (project), bsc-common-mistakes (project), bsc-nullability (project),
bsc-member-function (project), bsc-stdlib-advanced (project), bsc-lsp (project),
subset-skill-curation (project), c-to-bsc (project), bsc-operator-overloading (project),
bsc-overview (project), bsc-safe-zone (project), bsc-initialization (project),
bsc-design (project), bsc-stdlib (project), bsc-compile (project), 
bsc-ownership (project), ...
```

**关键特征**：
- 只列出名称，不列出描述（比 Claude Code 的目录索引更简洁）
- 标注 `(project)` 表示来源是项目级 skill

### 3.3 第三层：Slash Command → auto-slash-command + skill-instruction 双重注入

OpenCode 对 `/bsc-design` 命令的处理方式与 Claude Code **显著不同**——它注入了**两份** skill 内容：

**第一份**：`<auto-slash-command>` 包裹的命令元数据 + skill 全文

```json
{
  "text": "<auto-slash-command>\n# /bsc-design Command\n\n**Description**: (opencode-project - Skill) BiSheng C design and architecture decisions...\n**User Arguments**: 帮我基于此项目 继续开发出bsc的ftp服务器需求 \n**Scope**: skill\n\n---\n\n## Command Instructions\n\n<skill-instruction>\nBase directory for this skill: /home/rbtest0034/test/bsc_str_lib-master/.opencode/skills/bsc-design/\n\n# BiSheng C Design Skill\n[skill 全文...]\n</skill-instruction>\n</auto-slash-command>"
}
```

**第二份**：独立的 `<skill-instruction>` 包裹的 skill 全文（再次注入）

```json
{
  "text": "<skill-instruction>\nBase directory for this skill: /home/rbtest0034/test/bsc_str_lib-master/.opencode/skills/bsc-design/\n\n# BiSheng C Design Skill\n[skill 全文...]\n</skill-instruction>\n\n<user-request>\n帮我基于此项目 继续开发出bsc的ftp服务器需求 \n</user-request>"
}
```

**关键特征**：
- **同一份 skill 内容被注入了两次**——一次在 `<auto-slash-command>` 内，一次在独立的 `<skill-instruction>` 内
- 第二次注入末尾附带了 `<user-request>` 原始用户输入
- 这种双重注入可能是为了确保不同上下文窗口位置都能看到 skill 内容

### 3.4 第四层：Assistant 响应 → skill 工具二次加载

OpenCode 的 assistant 使用 OpenAI 格式的 `tool_calls`，模型主动调用 `skill` 工具加载更多 skill：

```json
{
  "role": "assistant",
  "content": "I detect an **implementation** intent...",
  "tool_calls": [
    {
      "function": {
        "name": "skill",
        "arguments": "{\"name\":\"bsc-overview\"}"
      }
    }
  ],
  "reasoning_content": "The user activated `/bsc-design` skill... Let me first explore the project."
}
```

然后 tool 返回 bsc-overview 的全文：

```json
{
  "role": "tool",
  "content": "## Skill: bsc-overview\n\n**Base directory**: ...\n\n# BiSheng C — Constrained-subset overview\n..."
}
```

**关键特征**：
- 模型通过 `reasoning_content`（思维链）解释为什么需要加载额外 skill
- skill 工具的返回值作为 `tool` role 消息注入
- 这是**模型主动发起**的二次加载，不是用户触发的

### 3.5 OpenCode 完整组装流程图

```
用户输入 "/bsc-design 帮我基于此项目继续开发FTP服务器"
    │
    ▼
┌──────────────────────────────────────────┐
│ 1. System Prompt 固定注入                 │
│    → agent-identity (Sisyphus)           │
│    → Role + Behavior_Instructions        │
│    → Skill 列表 (名称 only)              │
│    → 编排逻辑 (意图分类/委托规则)          │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ 2. auto-slash-command 注入（第1份skill）  │
│    → <auto-slash-command> 包裹            │
│    → 命令元数据 + Description + Args      │
│    → <skill-instruction> skill 全文       │
│    → user message 第1个 text block        │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ 3. skill-instruction 注入（第2份skill）   │
│    → <skill-instruction> skill 全文       │
│    → <user-request> 原始用户输入          │
│    → user message 第2个 text block        │
└──────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────┐
│ 4. 模型响应                               │
│    → reasoning_content 思维链推理         │
│    → 主动调用 skill 工具加载 bsc-overview │
│    → tool_calls → tool 循环              │
└──────────────────────────────────────────┘
```

---

## 四、核心差异对比表

| 维度 | Claude Code | OpenCode |
|------|------------|---------|
| **API 协议** | Anthropic Messages API | OpenAI Chat Completions API |
| **后端模型** | claude-opus-4-8 | deepseek-v4-flash (big-pickle) |
| **System Prompt** | 极简（仅工具声明+skill目录） | 重量级（完整编排逻辑+Sisyphus角色） |
| **CLAUDE.md 注入位置** | user message `<system-reminder>` | 无等价物（项目指令在 system 中） |
| **Skill 首次加载触发** | 用户 slash command | 用户 slash command |
| **Skill 注入方式** | 单次注入（1份全文） | 双重注入（2份全文，不同标签包裹） |
| **Skill 二次加载** | 模型调用 `Skill` 工具 | 模型调用 `skill` 工具 |
| **Skill 目录格式** | 名称 + 描述（详细） | 名称 only（简洁） |
| **思维链** | `thinking` block（redacted，不可见内容） | `reasoning_content`（可见推理过程） |
| **工具调用格式** | `tool_use` content block | `tool_calls` in choices |
| **Agent 机制** | frontmatter 声明 tools+model | 无 tools/model 声明 |
| **编排逻辑位置** | 分散在 superpowers skill 中 | 集中在 system prompt 中 |
| **插件机制** | 文件约定（零依赖） | npm 包 + 文件约定 |
| **Token 效率** | 按需加载，较省 token | 双重注入 + 重量级 system，较费 token |

---

## 五、实例追踪：同一用户请求的两种组装路径

### 用户请求：`/bsc-design 帮我基于此项目 继续开发出bsc的ftp服务器需求`

#### Claude Code 路径

```
Turn 1 (user):
  text[0]: <system-reminder> CLAUDE.md 全文（含"何时加载skill"指引）
  text[1]: <command-message>bsc-design</command-message> + 命令参数
  text[2]: bsc-design/SKILL.md 全文（单次注入）

Turn 2 (assistant):
  thinking: [redacted]（内容不可见，仅返回 signature）
  text: "I'll help you build an FTP server... let me start with brainstorming..."
  tool_use: Skill("superpowers:brainstorming")  ← 加载编排 skill
  tool_use: Bash("ls -la && find . -type f...")  ← 并行探索项目

Turn 3 (user):
  tool_result: Skill brainstorming 内容
  tool_result: Bash 输出

Turn 4 (assistant):
  thinking: [redacted]
  text: "The BSC compiler works... I now understand the project..."
  tool_use: AskUserQuestion({...})  ← 向用户提问范围问题
```

#### OpenCode 路径

```
Turn 1 (system):
  content: agent-identity + Role + Behavior_Instructions + Skill列表

Turn 2 (user):
  text[0]: <auto-slash-command> + bsc-design 全文（第1份）
  text[1]: <skill-instruction> + bsc-design 全文（第2份）+ <user-request>

Turn 3 (assistant):
  reasoning_content: "I detect implementation intent... Let me first explore..."
  content: "I detect an **implementation** intent..."
  tool_calls: skill("bsc-overview")  ← 主动加载额外 skill

Turn 4 (tool):
  content: bsc-overview/SKILL.md 全文

Turn 5 (assistant):
  reasoning_content: "Good, now I understand the constraints..."
  content: "Let me explore the current project structure..."
  tool_calls: read(dir), glob(pattern)  ← 并行探索
```

### 关键差异实例分析

1. **Skill 加载策略**：
   - Claude Code：slash command 触发时**一次性注入** skill 全文，后续 skill 通过 `Skill` 工具按需加载
   - OpenCode：slash command 触发时**双重注入** skill 全文，且模型在思维链中**主动决定**加载额外 skill（bsc-overview）

2. **编排逻辑**：
   - Claude Code：模型读取 CLAUDE.md 中的 "When to Load Other Skills" 指引后，先加载 `superpowers:brainstorming` 编排 skill，再按其流程执行
   - OpenCode：模型直接使用 system prompt 中的 "Phase 0 - Intent Gate" 编排逻辑，在思维链中完成意图分类（"I detect implementation intent"），然后自主决定下一步

3. **思维链可见性**：
   - Claude Code：`thinking` block 内容被 redact，只返回加密 signature——**思维过程对用户不可见**
   - OpenCode：`reasoning_content` 逐 token 流式返回——**思维过程对用户完全可见**（如 "The user activated `/bsc-design` skill which gives design guidelines for the constrained BSC subset. Let me first explore the project."）

4. **Token 消耗**：
   - Claude Code 的 bsc-design skill 在请求体中出现 **1 次**
   - OpenCode 的 bsc-design skill 在请求体中出现 **2 次**（auto-slash-command + skill-instruction）
   - 加上 OpenCode 的重量级 system prompt，同一请求的 token 消耗 OpenCode 显著更高（cc.req Content-Length: 155563 vs opencode.req Content-Length: 651487，约 4.2 倍）

---

## 六、Skill 知识体系分析（两套共享）

### 6.1 三层分类体系

项目使用 `subset-skill-curation` 技能定义了严格的三层分类：

| 类型 | 数量 | 含义 | 示例 |
|------|------|------|------|
| **Stub** | 7 | 整个主题在子集中被禁用 | bsc-coroutine, bsc-generic, bsc-trait, bsc-member-function, bsc-operator-overloading, bsc-stdlib, bsc-stdlib-advanced |
| **Banner** | 3 | 核心内容可用，但示例依赖禁用特性，需顶部适配表 | bsc-borrowing, bsc-common-mistakes, c-to-bsc |
| **Surgical** | 11 | 内容本身已适配子集，无需特殊处理 | bsc-design, bsc-ownership, bsc-safe-zone 等 |

### 6.2 知识图谱结构

```
bsc-overview (入口/导航)
├── bsc-ownership ──→ bsc-safe-zone, bsc-nullability
├── bsc-borrowing ──→ bsc-ownership, bsc-safe-zone, bsc-nullability, bsc-errors
├── bsc-safe-zone ──→ bsc-ownership, bsc-borrowing
├── bsc-nullability ──→ bsc-ownership, bsc-safe-zone
├── bsc-initialization ──→ (独立)
├── bsc-compile ──→ bsc-errors, bsc-common-mistakes
├── bsc-errors ──→ bsc-compile, bsc-common-mistakes
├── bsc-design ──→ bsc-ownership, bsc-safe-zone, bsc-borrowing
├── c-to-bsc ──→ (几乎所有其他 skill)
├── bsc-lsp ──→ (工具性，独立)
├── [7个 Stub] ──→ bsc-overview (重定向)
└── subset-skill-curation ──→ bsc-overview (维护流程)
```

### 6.3 规模统计

| 指标 | 数值 |
|------|------|
| Skill 总数 | 21 |
| Agent 总数 | 2 |
| 有效内容 Skill（非 Stub） | 14 |
| 最大文件 | c-to-bsc（~1547 行） |
| 最小文件 | bsc-generic（~10 行，Stub） |
| 总知识量 | ~5000+ 行 |

---

## 七、平台特有文件差异

### 7.1 Agent Frontmatter 差异

**Claude Code 版本**（bsc-learn.md）：
```yaml
---
name: bsc-learn
description: "..."
tools: Read, Grep, Glob, Bash    # ← Claude Code 专有
model: sonnet                      # ← Claude Code 专有
---
```

**OpenCode 版本**：
```yaml
---
name: bsc-learn
description: "..."
# 无 tools 和 model 字段
---
```

| Agent | Claude Code `tools` | Claude Code `model` | OpenCode 对应 |
|-------|---------------------|---------------------|--------------|
| bsc-learn | Read, Grep, Glob, **Bash** | sonnet | 无（由平台运行时决定） |
| bsc-planner | Read, Grep, Glob, **LSP** | sonnet | 无（由平台运行时决定） |

### 7.2 包管理配置

| 文件 | `.claude/` | `.opencode/` |
|------|-----------|-------------|
| package.json | 无 | `{"dependencies": {"@opencode-ai/plugin": "1.15.5"}}` |
| package-lock.json | 无 | 有（14KB） |
| node_modules/ | 无 | 有（@opencode-ai/plugin 包） |
| .gitignore | 无 | 有（忽略 node_modules 等） |

---

## 八、设计洞察

1. **Claude Code 的"延迟绑定"哲学**：skill 内容不预加载，只在需要时注入。CLAUDE.md 充当"路由表"，告诉模型何时加载什么。这使初始上下文更轻量，但依赖模型的判断力。

2. **OpenCode 的"预填充"哲学**：system prompt 预装完整编排逻辑，slash command 双重注入确保 skill 内容在上下文中足够"显眼"。这牺牲了 token 效率，但降低了模型"遗漏"skill 内容的风险。

3. **双重注入的可能原因**：OpenCode 的 `<auto-slash-command>` 和 `<skill-instruction>` 双重注入，可能是因为不同模型对 XML 标签的注意力权重不同——外层标签确保模型看到"这是一个命令"，内层标签确保模型看到"这是 skill 知识"。

4. **Agent 机制的差异根源**：Claude Code 的 Agent frontmatter 声明 `tools` 和 `model`，是因为 Claude Code 的子代理是**独立 API 调用**（独立会话、独立模型选择）。OpenCode 剥离这些字段，可能是因为其子代理在同一会话内运行，工具和模型由运行时统一管理。

5. **知识-平台分离**：项目作者将 BSC 领域知识（skill 内容）与平台适配逻辑（frontmatter 扩展字段、包管理）分离，同一套知识资产可同时服务多个 AI 编码工具。这是一种**可移植的 AI 知识管理**策略。

6. **Stub 模式的精妙**：7 个 Stub 类型 skill 不是简单的删除，而是保留为"路标"——当用户或 AI 尝试使用被禁用的功能时，Stub 提供明确的替代方案指引，避免"知识空洞"。

7. **从 HTTP 请求看组装差异**：Claude Code 的请求体中 skill 内容通过 `Skill` 工具按需加载注入；OpenCode 的请求体中 skill 内容通过 slash command 触发加载。两者都将 skill 作为**上下文注入**而非硬编码系统提示。
