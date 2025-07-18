#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// List of files that need getI18n import
const filesToFix = [
  'src/lib/components/AddFilesPlaceholder.svelte',
  'src/lib/components/AddServerModal.svelte',
  'src/lib/components/notes/NoteEditor.svelte',
  'src/lib/components/notes/NoteEditor/Chat/Messages.svelte',
  'src/lib/components/notes/NoteEditor/Chat/Message.svelte',
  'src/lib/components/notes/NoteEditor/Settings.svelte',
  'src/lib/components/notes/NoteEditor/Chat.svelte',
  'src/lib/components/notes/Notes.svelte',
  'src/lib/components/notes/Notes/NoteMenu.svelte',
  'src/lib/components/notes/AIMenu.svelte',
  'src/lib/components/notes/RecordMenu.svelte',
  'src/lib/components/workspace/Knowledge/ItemMenu.svelte',
  'src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte',
  'src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte',
  'src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte',
  'src/lib/components/workspace/Models/Knowledge/Selector.svelte',
  'src/lib/components/workspace/Models/ToolsSelector.svelte',
  'src/lib/components/workspace/Models/FiltersSelector.svelte',
  'src/lib/components/workspace/Models/Capabilities.svelte',
  'src/lib/components/workspace/Models/Knowledge.svelte',
  'src/lib/components/workspace/Models/ActionsSelector.svelte',
  'src/lib/components/workspace/Models/ModelMenu.svelte',
  'src/lib/components/workspace/common/AccessControl.svelte',
  'src/lib/components/workspace/common/AccessControlModal.svelte',
  'src/lib/components/workspace/common/ValvesModal.svelte',
  'src/lib/components/workspace/common/ManifestModal.svelte',
  'src/lib/components/workspace/Knowledge.svelte',
  'src/lib/components/workspace/Models.svelte',
  'src/lib/components/workspace/Prompts.svelte',
  'src/lib/components/workspace/Prompts/PromptMenu.svelte',
  'src/lib/components/workspace/Tools/AddToolMenu.svelte',
  'src/lib/components/workspace/Tools/ToolMenu.svelte',
  'src/lib/components/workspace/Tools.svelte',
  'src/lib/components/admin/Settings.svelte',
  'src/lib/components/admin/Evaluations/FeedbackModal.svelte',
  'src/lib/components/admin/Evaluations/LeaderboardModal.svelte',
  'src/lib/components/admin/Evaluations/Leaderboard.svelte',
  'src/lib/components/admin/Evaluations/FeedbackMenu.svelte',
  'src/lib/components/admin/Evaluations/Feedbacks.svelte',
  'src/lib/components/admin/Users/UserList.svelte',
  'src/lib/components/admin/Users/Groups.svelte',
  'src/lib/components/admin/Users/UserList/EditUserModal.svelte',
  'src/lib/components/admin/Users/UserList/UserChatsModal.svelte',
  'src/lib/components/admin/Users/UserList/AddUserModal.svelte',
  'src/lib/components/admin/Users/Groups/AddGroupModal.svelte',
  'src/lib/components/admin/Users/Groups/Users.svelte',
  'src/lib/components/admin/Users/Groups/Display.svelte',
  'src/lib/components/admin/Users/Groups/Permissions.svelte',
  'src/lib/components/admin/Users/Groups/GroupItem.svelte',
  'src/lib/components/admin/Users/Groups/EditGroupModal.svelte',
  'src/lib/components/admin/Users.svelte',
  'src/lib/components/admin/Settings/Models/Manage/ManageMultipleOllama.svelte',
  'src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte',
  'src/lib/components/admin/Settings/Models/ManageModelsModal.svelte',
  'src/lib/components/admin/Settings/Models/ModelList.svelte',
  'src/lib/components/admin/Settings/Models/ConfigureModelsModal.svelte',
  'src/lib/components/admin/Settings/Models/ModelMenu.svelte',
  'src/lib/components/admin/Settings/Images.svelte',
  'src/lib/components/admin/Settings/Documents.svelte',
  'src/lib/components/admin/Settings/Connections.svelte',
  'src/lib/components/admin/Settings/Connections/ManageOllamaModal.svelte',
  'src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte',
  'src/lib/components/admin/Settings/Connections/OllamaConnection.svelte',
  'src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte',
  'src/lib/components/admin/Settings/Evaluations/Model.svelte',
  'src/lib/components/admin/Settings/Interface/Banners.svelte',
  'src/lib/components/admin/Settings/WebSearch.svelte',
  'src/lib/components/admin/Settings/Database.svelte',
  'src/lib/components/admin/Settings/Evaluations.svelte',
  'src/lib/components/admin/Settings/Models.svelte',
  'src/lib/components/admin/Settings/Interface.svelte',
  'src/lib/components/admin/Settings/General.svelte',
  'src/lib/components/admin/Settings/CodeExecution.svelte',
  'src/lib/components/admin/Settings/Tools.svelte',
  'src/lib/components/admin/Evaluations.svelte',
  'src/lib/components/admin/Functions/FunctionMenu.svelte',
  'src/lib/components/admin/Functions/AddFunctionMenu.svelte',
  'src/lib/components/admin/Functions/FunctionEditor.svelte',
  'src/lib/components/admin/Functions.svelte',
  'src/lib/components/common/Image.svelte',
  'src/lib/components/common/Tags.svelte',
  'src/lib/components/common/Folder.svelte',
  'src/lib/components/common/Tags/TagInput.svelte',
  'src/lib/components/common/Tags/TagList.svelte',
  'src/lib/components/common/FileItem.svelte',
  'src/lib/components/common/Collapsible.svelte',
  'src/lib/components/common/CodeEditor.svelte',
  'src/lib/components/common/Valves.svelte',
  'src/lib/components/common/FileItemModal.svelte',
  'src/lib/components/common/ConfirmDialog.svelte',
  'src/lib/components/common/SVGPanZoom.svelte',
  'src/lib/components/common/RichTextInput.svelte',
  'src/lib/components/common/RichTextInput/FormattingButtons.svelte',
  'src/lib/components/ImportModal.svelte',
  'src/lib/components/OnBoarding.svelte',
  'src/lib/components/AddConnectionModal.svelte',
  'src/lib/components/playground/Chat/Messages.svelte',
  'src/lib/components/playground/Chat/Message.svelte',
  'src/lib/components/playground/Completions.svelte',
  'src/lib/components/playground/Chat.svelte',
  'src/lib/components/chat/Artifacts.svelte',
  'src/lib/components/chat/ModelSelector/Selector.svelte',
  'src/lib/components/chat/ModelSelector/ModelItemMenu.svelte',
  'src/lib/components/chat/ModelSelector/ModelItem.svelte',
  'src/lib/components/chat/CustomStylesModal.svelte',
  'src/lib/components/chat/ChatPlaceholder.svelte',
  'src/lib/components/chat/ShortcutsModal.svelte',
  'src/lib/components/chat/Messages.svelte',
  'src/lib/components/chat/MessageInput.svelte',
  'src/lib/components/chat/SettingsModal.svelte',
  'src/lib/components/chat/Settings/Connections.svelte',
  'src/lib/components/chat/Settings/Connections/Connection.svelte',
  'src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte',
  'src/lib/components/chat/Settings/Account.svelte',
  'src/lib/components/chat/Settings/Account/UpdatePassword.svelte',
  'src/lib/components/chat/Settings/Chats.svelte',
  'src/lib/components/chat/Settings/Audio.svelte',
  'src/lib/components/chat/Settings/Personalization.svelte',
  'src/lib/components/chat/Settings/Interface.svelte',
  'src/lib/components/chat/Settings/General.svelte',
  'src/lib/components/chat/Settings/Personalization/AddMemoryModal.svelte',
  'src/lib/components/chat/Settings/Personalization/ManageModal.svelte',
  'src/lib/components/chat/Settings/Personalization/EditMemoryModal.svelte',
  'src/lib/components/chat/Settings/About.svelte',
  'src/lib/components/chat/Settings/Tools/Connection.svelte',
  'src/lib/components/chat/Settings/Tools.svelte',
  'src/lib/components/chat/ShareChatModal.svelte',
  'src/lib/components/chat/Navbar.svelte',
  'src/lib/components/chat/MessageInput/CallOverlay/VideoInputMenu.svelte',
  'src/lib/components/chat/MessageInput/CallOverlay.svelte',
  'src/lib/components/chat/MessageInput/InputVariablesModal.svelte',
  'src/lib/components/chat/MessageInput/VoiceRecording.svelte',
  'src/lib/components/chat/MessageInput/Commands/Knowledge.svelte',
  'src/lib/components/chat/MessageInput/Commands/Models.svelte',
  'src/lib/components/chat/MessageInput/Commands/Prompts.svelte',
  'src/lib/components/chat/MessageInput/InputMenu.svelte',
  'src/lib/components/chat/Placeholder.svelte',
  'src/lib/components/chat/Controls/Valves.svelte',
  'src/lib/components/chat/Controls/Controls.svelte',
  'src/lib/components/chat/ToolServersModal.svelte',
  'src/lib/components/chat/Overview.svelte',
  'src/lib/components/chat/ContentRenderer/FloatingButtons.svelte',
  'src/lib/components/chat/Suggestions.svelte',
  'src/lib/components/chat/TagChatModal.svelte',
  'src/lib/components/chat/Messages/MultiResponseMessages.svelte',
  'src/lib/components/chat/Messages/CodeBlock.svelte',
  'src/lib/components/chat/Messages/RateComment.svelte',
  'src/lib/components/chat/Messages/ResponseMessage/FollowUps.svelte',
  'src/lib/components/chat/Messages/CitationsModal.svelte',
  'src/lib/components/chat/Messages/Message.svelte',
  'src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte',
  'src/lib/components/chat/Messages/Markdown/HTMLToken.svelte',
  'src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens.svelte',
  'src/lib/components/chat/Messages/CodeExecutionModal.svelte',
  'src/lib/components/chat/Messages/ContentRenderer.svelte',
  'src/lib/components/chat/Messages/Citations.svelte',
  'src/lib/components/chat/Messages/UserMessage.svelte',
  'src/lib/components/chat/ModelSelector.svelte',
  'src/lib/components/layout/Sidebar.svelte',
  'src/lib/components/layout/Sidebar/UserMenu.svelte',
  'src/lib/components/layout/Sidebar/ChatItem.svelte',
  'src/lib/components/layout/Sidebar/RecursiveFolder.svelte',
  'src/lib/components/layout/Sidebar/SearchInput.svelte',
  'src/lib/components/layout/Sidebar/ChatMenu.svelte',
  'src/lib/components/layout/Sidebar/Folders/FolderMenu.svelte',
  'src/lib/components/layout/Sidebar/Folders/EditFolderModal.svelte',
  'src/lib/components/layout/Sidebar/ChannelItem.svelte',
  'src/lib/components/layout/Sidebar/ChannelModal.svelte',
  'src/lib/components/layout/Navbar.svelte',
  'src/lib/components/layout/ChatsModal.svelte',
  'src/lib/components/layout/UpdateInfoToast.svelte',
  'src/lib/components/layout/SearchModal.svelte',
  'src/lib/components/layout/Navbar/Menu.svelte',
  'src/lib/components/layout/ArchivedChatsModal.svelte',
  'src/lib/components/layout/Overlay/AccountPending.svelte',
  'src/lib/components/ChangelogModal.svelte',
  'src/lib/components/channel/Messages.svelte',
  'src/lib/components/channel/MessageInput.svelte',
  'src/lib/components/channel/Navbar.svelte',
  'src/lib/components/channel/MessageInput/InputMenu.svelte',
  'src/routes/error/+page.svelte',
  'src/routes/(app)/notes/+page.svelte',
  'src/routes/(app)/admin/functions/edit/+page.svelte',
  'src/routes/(app)/admin/functions/create/+page.svelte',
  'src/routes/(app)/admin/+layout.svelte'
];

// Function to add getI18n import to a file
function addGetI18nImport(filePath) {
  try {
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Check if getI18n import already exists
    if (content.includes('import { getI18n }')) {
      return false; // Already has import
    }
    
    // Check if file uses getI18n()
    if (!content.includes('getI18n()')) {
      return false; // Doesn't need import
    }
    
    // Find the script tag
    const scriptMatch = content.match(/<script[^>]*>/);
    if (!scriptMatch) {
      console.log(`No script tag found in ${filePath}`);
      return false;
    }
    
    const scriptStart = scriptMatch.index + scriptMatch[0].length;
    
    // Find the position to insert the import (after existing imports)
    const afterScript = content.slice(scriptStart);
    const importRegex = /^\s*import[^;]+;/gm;
    const imports = [...afterScript.matchAll(importRegex)];
    
    let insertPos = scriptStart;
    if (imports.length > 0) {
      const lastImport = imports[imports.length - 1];
      insertPos = scriptStart + lastImport.index + lastImport[0].length;
    }
    
    // Insert the import
    const importStatement = '\n\timport { getI18n } from \'$lib/i18n/helpers\';';
    content = content.slice(0, insertPos) + importStatement + content.slice(insertPos);
    
    fs.writeFileSync(filePath, content);
    return true;
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
    return false;
  }
}

// Process all files
let fixedCount = 0;
for (const filePath of filesToFix) {
  const fullPath = path.join(__dirname, filePath);
  if (fs.existsSync(fullPath)) {
    if (addGetI18nImport(fullPath)) {
      console.log(`Added getI18n import to ${filePath}`);
      fixedCount++;
    }
  } else {
    console.log(`File not found: ${filePath}`);
  }
}

console.log(`Fixed ${fixedCount} files`);
