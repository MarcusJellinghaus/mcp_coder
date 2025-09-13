
# Project idea: Automating the development of a software feature

## Summary 

## What to automate: A software feature
Developing software involves many steps. 
At its core, there is the development of a certain feature and/or the fixing of a certain bug.
A good starting point is usually an issue (eg in Github).

### Analysis and planning
Such an issue needs to be analysed, the related software code needs to be analysed and the developer can come up with a plan how to implement the feature.
Such a plan usually contains several steps.
The first steps might be the adjustment of different base functionality.
Later steps combine/integrate the base functionality in something bigger.
The last steps often include updating the documentation.

### Implementation in several steps
Each step usually involves writing and/or modifying code.
Following test driven development, it is good practice to write the test first, and implement the required code changes to fix the failing test in a second step.
Once a step has been completed, it makes sense to commit the changes code to git.

### Pull request
Once a feature has been implemented, the changes can be reviewed.
This is usually being done with a Pull request, which includes the changes for a certain feature and bundles them on git branch.
I.e. the first step of an implementation is actually the creation of a new branch on git.
After all the implementation steps commited their changes to the branch, the branch should be reviewed.
As a potential outcome of the review, more implementation steps might be created (similar to the analysis and planning steps). 
A summary explaining the changes of a pull request should be written.

Once all tests of the CI pipeline pass, and the pull request summary makes sense, the pull request can be approved and merged into the main code base.
this completes the implementation of a feature.

## Idea - automate software development using LLMs

Large Language Models (LLMs) are available since a few years now.
Some of them are focussed on smart, complex capabilities, eg for software development.
Anthropic's Claude is one of the software models that is well known for its coding features.

So LLMs can be used to write code. And software code be used to tell LLMs what do / automate them.
Is this already enough to create a "virtuous cycle"?

### Hallucination and feedback loops

LLMs sometimes make mistakes and/or hallucinate.
One option would be to hope for "perfect code" after the first attempt.
However, given the LLM feedback about the code allows the LLM to improve the code. 
Eg the [MCP-code-checker](https://github.com/MarcusJellinghaus/mcp-code-checker) checks python code using standard python packages like pylint, pytest and mypy and provides feedback on the code quality.

### Better interfaces and/or some autonomy for LLms: MCP Server
[Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro) (MCP) servers allow an LLM to call extra functionality, like the above mentioned MCP-code-checker.
While first versions of ChatGpt just had a chat interface, newer LLMs are accessible via MCP clients.
Claude Desktop, GtHub Copilot (in VSCode or Pycharm) or Claude Code allow to interact with an LLM, and allow the LLM to call MCP servers.
For the LLM, the calling to MCP servers is often restricted, eg requires specific approval by the users and/or a special mode (eg "Agent" mode).

Once the MCP servers are available, the LLM can eg read code, modify code, run checks, do further corrections, check some more etc until the code works as expected (or the LLM gives up).
This level of autonomy looks quite powerful - maybe better than just asking the LLM to do something, and telling then the LLM about the results.
Eg the LLM might first just trigger the specific unit tests, and later run all tests.

To hand over data between different functions, most programming languages use certain data types.
By default, LLMs produce text. While "the answer is 5" and "5" have a similar meaning for a human, it is not the same for a computer program that expects an integer as reply.
LLMs can provide an answer in JSON. However, there is also some mixed experience.
In some cases, MCP servers seem to allow for better technical interaction.

### Limited context window sizes
> A context window refers to the maximum amount of text (measured in tokens) that an AI model can process and consider at one time when generating a response. Think of it as the model's "working memory" or "attention span".

To allow an LLM to work efficiently, they need to have all the relevant information to work on their task at hand.
( And an MCP server can help them to find additional relevant information, eg by reading some files of the code base, or by searching the internet. )
When context window gets fuller and fuller, the conversation gets slower and slower, and exponentially more expensive.
A new message is not only one new message. For each new message, actually the whole conversation so far gets submitted / considered again by the LLM.

For that reason, it makes sense to stop an LLM conversation and start a new one, as often as possible.
Obviously, one does not always want to create a summary of all relevant information. 
Therefore, one has to strike a balance between "keeping the context" and "starting a new conversation".

### LLM running commands, automated steps, sub-agents

#### Why and how to automate with an LLM
An LLM can read a long text and search for certain information in the text.
However, it is more efficient to execute dedicated commands whenever they are available.
Eg to search for all "TODO" in some software code can be done very efficiently.

With some MCP clients, the LLM can run commands. This allows the LLM to search for "TODO" in a code base running some simple commands. 
For the perfect LLM, one could allow the LLM to run any command on a computer.
However, since LLMs make mistakes, it might be better to do it in a more protected way, eg with dedicated MCP Serverand/or specific access rights rules for the LLM.

#### Change of focus and refocus
When working on a specific problem, we sometimes need to change focus and analyse a subtopic or slightly different topic.
It might make sense to have several agents working on different topics.
Ths could just be a separate chat with a specific prompt, and the response is summarised and returned to the main chat.

Some experience from first "automatic coding":
Just by providing the static "fixing instructions" for each error code instead of the error code can make already quite some difference for an LLM that needs to improve a code base.

Sometimes, LLMs forget some instructions that they received.
Refocussing the LLM might help.
In one case, a text document with a todo list (with `[ ]` and `[X]` that had to be checked) helped the LLM to not forget steps.

## How to automate

The file [Development process](../PR_Info/Development_Process.md) outlines a development process that has already been tested.
The prompts and the interaction with LLM and environment are working.
However, it is so far only a semi-automated process.

As per the document, it consists of three main processes:
- Feature planning
- Implementation steps
- Feature completion

### Automation of `implementation steps`

As a first step, the `implementation steps` should be automated.

Within that, the different features should be implemented in a `learning` way:


#### Automation of commits

There are two use cases:
- 
- `Commit` based on a specified `commit message`
- `Commit` without a specific `commit message`

Sub functions
- `Commit`
  - commit files
    - by default, all files (could be enhanced later)
    - based on a specified `commit message`
    - within specified project directory 
      - probably checking `is_git_repository(project_dir: Path)` from [git_operations` in mcp_server_filesystem](https://github.com/MarcusJellinghaus/mcp_server_filesystem/blob/main/src/mcp_server_filesystem/file_tools/git_operations.py)
    - with specified check for `files to commit?` (subfunction)
    - others
- `Get diff` - similar to `tools\commit_summary.bat`, all changes should be identified and put into a git diff (??) style string
  - to be analysed further, batch file implementation already exists
  - will be part of `git_operations`
  - prompt should be added from `prompt_manager`
- `Prompt manager`
  - Idea: 
    - Prompts should not be hardcoded at different places all over the code.
    - Instead, a number of central markdown files should be available.
    - This should allow for easy editing.
    - Maybe we can come up with some structure
    - Headers (after `# Header`) should be the key to find a paragraph
    - The prompt is written like code with 3 quotes before and after.
    - A `get_prompt(filename, prompt_header)` function should be able retrieve the prompt.
    - A `validate_prompt_markdown(filename)` function should be able to verify the prompt file.
    - It needs to be identified what needs to be done so that the prompt file gets deployed with the software 
      when installing it. 
      This probably also an impact on the specification of the paths, the location, etc.
- `ask_llm` send the prompt to the llm and get back a reply 
  - for now with claud code / using the abo licenxse
  - API:
    - cli
    - try to move to python API (if available)
  - hope to extend
    - send more complex existing chat
    - receive complete chat
    - allow it to use MCP server(s)
  - abstraction layer to allow to use other LLMs and/or licenses
  
- `auto_commit` would get the prompt and the diff, ask the llm for a commit message, and commit the code

#### Automation of commit preparation

- check for valid code
  - check with `mcp-code-checker` whether all checks pass
- format code with black and isort
  - maybe additional functions within mcp-code-checker 

- (later) get commit message from chat, or ask chat for commit message

### Automation of implementation

- (later)
- Should be easy
- good understanding of chat / steps / mcp communication
- good logging
- detection of errors?
- analysis of logs with llm for errors
- get commit message
- check of task_tracker for remaining tasks


## Architecture \ design
- 
- use GitPython for git interaction
- use `mcp-code-checker` whether all checks pass
- dedicated sub-module `git_operations`
- Folder structure like other related relates repos, with src and tests, tools, pr_info folder
- code for mcp-coder in src, submodules within that folder

