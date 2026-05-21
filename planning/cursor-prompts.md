# Cursor Prompts for Practice Manager

This file contains helpful prompts for using Cursor's AI features to manage this project effectively.

## 📝 Review project status

Use this prompt to refresh the current project status:

> Review `README.md`, `docs/`, `src/practice_manager/`, `tests/`, and `planning/`. Summarize current product status, verification status, known gaps, and the next three highest-leverage actions. Do not invent status beyond local evidence.

## 📋 Create PRD (Product Requirements Document)

Use this prompt to create a PRD using the local template:

**See: `prompts/create-prd.md` for the complete prompt**

This prompt uses the local create-prd.mdc template for consistency across projects.

## ✅ Create Tasks File

Use this prompt to create a tasks file using the local template:

**See: `prompts/create-tasks.md` for the complete prompt**

This prompt uses the local generate-tasks.mdc and task-list.mdc templates for consistent task organization.

## 🔄 Update All Planning Files

Use this prompt to comprehensively update all planning files:

> Update `planning/status.md`, `planning/suggested-next-actions.md`, `planning/prd-practice-manager.md`, and `planning/tasks-practice-manager.md` so they reflect the current Practice Manager implementation and verification state.

## 

## 💡 Tips for Using These Prompts

1. **Be Specific**: Include relevant context about your project goals and constraints
2. **Ask Questions**: Let the AI ask clarifying questions to get better results
3. **Iterate**: Use the AI's suggestions as a starting point and refine as needed
4. **Review**: Always review and validate the AI's recommendations
5. **Update Regularly**: Use these prompts regularly to keep planning files current

## 🔗 Related Files

- `create-prd.mdc` - Template for creating PRDs
- `generate-tasks.mdc` - Template for generating tasks
- `task-list.mdc` - Template for task list structure
- `prd-practice-manager.md` - Product status and requirements
- `tasks-practice-manager.md` - Implementation and verification tasks
- `status.md` - Current review snapshot
- `suggested-next-actions.md` - Current action queue

## 📁 Prompts Directory

If a future `prompts/` directory is added, keep project-specific prompts aligned with Practice Manager rather than the older Script Manager template language.
