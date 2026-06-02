# 两个 YAML 提示词组织方式对比分析

## 1. 文件基本信息

| 文件 | 工具 | 模型 | 角色定位 |
|------|------|------|---------|
| `opencode-req.yaml` | OhMyOpenCode (OpenCode) | `big-pickle` | 编排型 Agent "Sisyphus" |
| `cc-req.yaml` | Claude Code | `claude-opus-4-8` | 通用编码助手（无人格名） |

## 2. 提示工程范式差异

| 维度 | opencode-req (OpenCode) | cc-req (Claude Code) |
|------|------------------------|----------------------|
| **范式** | **行为编程**（Behavioral Programming） | **原则式引导**（Principle-based Guidance） |
| **风格** | 命令式："MUST"、"NEVER"、"MANDATORY" | 建议式："Prefer"、"Consider"、"Ask yourself" |
| **触发机制** | 显式的 if-then 触发条件和路由表 | 隐含在原则中的推理 |
| **粒度** | 极高的颗粒度，每一步都有明确的指令 | 较粗的颗粒度，靠模型自主推理 |

## 3. 组织结构对比

### opencode-req.yaml — 层级化阶段系统

采用 **Phase 编号** 结构 + XML 标签分区：

```
<agent-identity>          # 身份声明
<Role>                    # 角色定义
<Behavior_Instructions>   # 核心行为（含6个阶段）
  ├── Phase 0 — Intent Gate        # 意图分类 + 路由
  ├── Phase 1 — Codebase Assessment # 代码库成熟度评估
  ├── Phase 2A — Exploration        # 多Agent并行探索
  ├── Phase 2B — Implementation     # 委派执行 + Todo管理
  ├── Phase 2C — Failure Recovery   # 失败恢复协议
  └── Phase 3 — Completion          # 完成验证
<Oracle_Usage>            # 顾问Agent使用规则
<Task_Management>         # Todo管理规范
<Tone_and_Style>          # 沟通风格
<Constraints>             # 硬性约束
```

### cc-req.yaml — 扁平化 Markdown 结构

采用 **Markdown 标题层级** 组织：

```
Working Principles（4条原则）
  ├── 1. Think Before Coding
  ├── 2. Simplicity First
  ├── 3. Surgical Changes
  └── 4. Goal-Driven Execution

BSC Language Reference（语言规则参考）
  ├── Pointer Qualifier Grammar
  ├── Quick Reference
  ├── BSC Project Compile Command
  ├── Code Verification
  ├── LSP Usage
  ├── When to Load Other Skills
  ├── When to Delegate to bsc-planner
  └── When to Invoke bsc-learn

BSC Design Skill（嵌入的技能文件内容）
  ├── 9条经验法则（Rules of Thumb）
  ├── 类型设计（Type Design）
  ├── API设计（API Design）
  ├── 所有权流设计（Ownership Flow）
  ├── Safe/Unsafe边界设计
  ├── 反模式（Anti-Patterns）
  └── 完整示例
```

## 4. 核心内容差异

### 4.1 焦点不同：工具使用 vs 领域知识

**opencode-req.yaml** — 教的是"如何使用这个工具本身"：
- 如何分类意图（Intent Gate 路由表）
- 如何委派子 Agent（Category + Skills 选择协议）
- 如何管理后台任务（`bg_`/`ses_` ID 系统）
- 如何使用 Oracle 顾问 Agent
- 如何创建和管理 Todo 列表
- 如何做失败恢复

**cc-req.yaml** — 教的是"如何写好 BSC 代码"：
- BSC 语言语法规则（指针限定符位置）
- 设计模式（9条经验法则）
- API 设计决策（值返回 vs 指针返回）
- 所有权流设计
- Safe/Unsafe 边界设计
- 反模式清单
- 编译验证流程

### 4.2 Agent 自我认知差异

**opencode-req.yaml**：
> "Your failure mode: You attempt to do work yourself instead of decomposing and delegating."
> "Your value is orchestration, decomposition, and quality control."
> "You write prompts, not code."

→ 明确的编排者定位，鼓励 **不写代码、只做委派**

**cc-req.yaml**：
> "Touch only what you must."
> "Minimum code that solves the problem."
> "If you write 200 lines and it could be 50, rewrite it."

→ 明确的实现者定位，鼓励 **直接写高质量代码**

### 4.3 执行模型差异

| 方面 | opencode-req | cc-req |
|------|-------------|--------|
| **执行方式** | 并行多 Agent（默认 `run_in_background=true`） | 串行单 Agent 直接工具调用 |
| **任务协调** | 事件驱动（background task → system-reminder → 收集结果） | 顺序执行（读 → 想 → 写 → 验） |
| **委派机制** | Category（领域优化模型）+ Skills（技能加载）+ Plan Agent | 委派给 `bsc-planner` Agent（仅限复杂跨模块任务） |
| **续会话机制** | 显式 `task(task_id="ses_...")` 续会话 | 隐式上下文延续 |
| **并行度** | 强制并行："If 4 independent units exist, spawn 4 agents simultaneously" | 无并行要求 |

### 4.4 约束和错误处理差异

**opencode-req.yaml** — 形式化、协议化的错误处理：

```
After 3 Consecutive Failures:
1. STOP all further edits immediately
2. REVERT to last known working state
3. DOCUMENT what was attempted
4. CONSULT Oracle with full failure context
5. If Oracle cannot resolve → ASK USER
```

+ 硬性约束清单（Hard Blocks）：
  - Never: `as any`, `@ts-ignore`, 未授权的 commit, 未收集 Oracle 结果前交付答案
  - Never: `background_cancel(all=true)`, 轮询运行中的 background task

**cc-req.yaml** — 隐含在原则中的约束：

> "If you write 200 lines and it could be 50, rewrite it."
> "Don't 'improve' adjacent code, comments, or formatting."
> "Don't refactor things that aren't broken."

无显式的失败恢复协议，依赖模型自主判断。

### 4.5 Todo 管理差异

| 方面 | opencode-req | cc-req |
|------|-------------|--------|
| **强制程度** | 强制（"NON-NEGOTIABLE"） | 可选（"For multi-step tasks, state a brief plan"） |
| **粒度** | 细粒度原子步骤 | 简要的步骤 + 验证点 |
| **工具** | 专门的 `todowrite` 工具 | 纯文本陈述 |
| **更新时机** | 每一步立即更新（`in_progress` → `completed`） | 无明确更新规范 |

## 5. 总结

| 核心区别 | opencode-req.yaml | cc-req.yaml |
|---------|------------------|-------------|
| **哲学** | 编排至上（Orchestration-first） | 实现至上（Implementation-first） |
| **提示工程流派** | 行为编程（显式 trigger → action 映射） | 原则引导（隐式规则 → 模型推理） |
| **复杂度** | 极高（覆盖多 Agent 全生命周期） | 中等（聚焦单 Agent 编码质量） |
| **约束表达** | 硬性规则（Hard Blocks + 形式化协议） | 软性原则（Working Principles） |
| **领域注入** | 注入的是工具使用方法论 | 注入的是 BSC 语言设计领域知识 |
| **可迁移性** | 工具特定（依赖 OpenCode 的 Agent 系统） | 相对通用（编码原则可跨工具复用） |

### 4.6 Skill 注入的冗余问题

实际注入时发现，OpenCode 的 bsc-design skill 内容在 `messages` 中出现了 **4 次**：

| msg | role | 内容 |
|-----|------|------|
| msg[0] | system | `<skill-instruction>` 块嵌在主 system prompt |
| msg[1] part[1] | user | `/bsc-design` 命令描述（含 skill 结尾句） |
| msg[1] part[2] | user | 完整的 `<skill-instruction>` 块（与 msg[0] 重复） |
| msg[5] | tool | 工具结果回显的目录信息也带上了该句 |

其中 msg[0] 和 msg[1] part[2] 是同一份 `<skill-instruction>` 的完全重复（~529 行 BSC 设计规则）。这表明 OpenCode 的 prompt 组装缺乏去重机制：

- system prompt 注入器加了一次
- command 处理器又加了一次（作为 user message）
- 工具执行结果又带回来一次

**同一份 skill 内容消耗了 2~3 倍的 token 预算**，在上下文中是明显的浪费。

对比 Claude Code：skill 内容只在 user message 的一个 `text` part 中出现 **1 次**，无 system prompt 冗余注入，无工具结果回显冗余。

**一句话概括**：`opencode-req.yaml` 是在教一个 **指挥部如何调度战斗**（编排、委派、协调、恢复），而 `cc-req.yaml` 是在教一个 **士兵如何打好每一场仗**（设计、实现、验证、简洁）。
